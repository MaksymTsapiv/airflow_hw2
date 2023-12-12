from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.models import Variable
from easyocr import Reader
from bs4 import BeautifulSoup
from peopledatalabs import PDLPY
import requests
from commonregex import CommonRegex


def _get_images():
    pg_conn_id = 'marketing_pg_conn'

    target_url = Variable.get("TARGET_URL")
    page_response = requests.get(target_url)
    soup = BeautifulSoup(page_response.content, 'html.parser')
    image_tags = soup.find_all('img')
    image_urls = [tag['src'] for tag in image_tags if 'src' in tag.attrs]

    pg_hook = PostgresHook(postgres_conn_id=pg_conn_id)

    new_images = []
    for old_img in pg_hook.get_records(
            sql="sql/select.sql"):
        for img in image_urls:
            if old_img[0] == img:
                continue
            new_images.append(img)

    for new_url in new_images:
        pg_hook.run(
            sql="sql/insert_images.sql",
            parameters=[new_url],
        )


def _process_images():
    pg_conn_id = 'marketing_pg_conn'
    all_links = []

    pg_hook = PostgresHook(postgres_conn_id=pg_conn_id)
    records = pg_hook.get_records(
        sql="sql/select_unprocessed.sql")

    for record in records:
        image_url = record[0]
        reader = Reader(['en'])
        ocr_results = reader.readtext(image_url)
        text = ' '.join([res[1] for res in ocr_results])
        parsed_text = CommonRegex(text)
        links = parsed_text.links
        all_links.append(links)

        pg_hook.run(
            sql="sql/update.sql",
            parameters=[image_url],
        )

    return all_links


def _get_company_info(**kwargs):
    pg_conn_id = "marketing_pg_conn"
    pdl_key = Variable.get("PDL_API_KEY")
    urls = kwargs["ti"].xcom_pull("ocr_images")
    client = PDLPY(api_key=pdl_key)
    pg_hook = PostgresHook(postgres_conn_id=pg_conn_id)

    for url in urls:
        params = {"website": url}
        json_response = client.company.enrichment(**params).json()
        name = json_response.get("name")
        size = json_response.get("size")
        display_name = json_response.get("display_name")

        if name and display_name and size:
            pg_hook.run(
                sql="sql/update.sql",
                parameters=[url, name, size, display_name],
            )


with DAG(dag_id="marketing_hw2",
         schedule_interval="@daily",
         start_date=datetime(2023, 11, 27),
         catchup=True,
         ) as dag:
    create_image_table = PostgresOperator(
        task_id="create_image_table",
        postgres_conn_id="marketing_pg_conn",
        sql="sql/images.sql",
    )

    create_info_table = PostgresOperator(
        task_id='create_info_table',
        postgres_conn_id='marketing_pg_conn',
        sql="sql/info.sql"
    )

    get_images = PythonOperator(
        task_id='get_images',
        python_callable=_get_images,
    )

    ocr = PythonOperator(
        task_id='ocr_images',
        python_callable=_process_images,
    )

    get_company_info = PythonOperator(
        task_id="company_info",
        python_callable=_get_company_info,
    )

    create_image_table >> create_info_table >> get_images >> ocr >> get_company_info

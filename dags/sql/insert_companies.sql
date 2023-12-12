INSERT INTO companies (company_url, company_name, size, display_name)
VALUES (%s, %s, %s, %s) ON CONFLICT (company_url) DO NOTHING

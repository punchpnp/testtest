
mock_database = {
    "company_income_statement": [
        "centel",
        "iberry"
    ]
}

def company_file_exists(company_name: str):

    return company_name.lower() in mock_database["company_income_statement"]

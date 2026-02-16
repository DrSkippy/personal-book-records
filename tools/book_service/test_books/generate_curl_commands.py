import json
import subprocess
import random

cleanup = ["""DELETE FROM complete_date_estimates WHERE LastReadablePage=15000\;"""]

def generate_curl_commands():

    config_file = "./config/configuration.json"

    with open(config_file, "r") as infile:
        config = json.load(infile)
        API_KEY = config["api_key"]
        ENDPOINT = config["endpoint"]

    sample_data = {"<target_year>": "2022",
                   "<book_id>": "1873",
                   "<tag>": "fiction",
                   "<year>": "2020",
                   "<match_str>": "Lewis",
                   "<current>": "recovery",
                   "<updated>": "recovery",
                   "<window>": "20",
                   "<record_id>": "50",
                   "<last_readable_page>": "15000",
                   "<start_date>": "1945-10-19",
                   "<adjacent>": "next",
                   "<limit>": "10"
    }

    print("# Sample data for endpoints:")
    for k, v in sample_data.items():
        print(f"#   {k}: {v}")
    print("\n")

    print("# Getting all of the GET endpoints from book_service/books/api.py")
    command = "cat ./books/api.py | grep app.route | grep -v POST | grep -v PUT | cut -d\\' -f2"
    result = subprocess.check_output(command, shell=True)
    result = result.decode("utf-8").strip().split("\n")

    get_endpoints = []
    for line in result:
        for k, v in sample_data.items():
            line = line.replace(k, v)
        print("# "+line)
        get_endpoints.append(line)
    print("\n")

    print("# Getting all of the PUT endpoints from book_service/books/api.py")
    command = "cat ./books/api.py | grep app.route | grep PUT | cut -d\\' -f2"
    result = subprocess.check_output(command, shell=True)
    result = result.decode("utf-8").strip().split("\n")

    put_endpoints = []
    for line in result:
        for k, v in sample_data.items():
            line = line.replace(k, v)
        print("# "+line)
        put_endpoints.append(line)
    print("\n")

    print("# Generating curl commands for common API calls:\n")
    get_template = {"method": "GET", "endpoint_suffix": None, "headers": f"x-api-key: {API_KEY}", "ENDPOINT": ENDPOINT}
    cases = []
    for endpoint in get_endpoints:
        _template = get_template.copy()
        _template["endpoint_suffix"] = endpoint
        cases.append(_template)

    put_template = {"method": "PUT", "endpoint_suffix": None, "headers": f"x-api-key: {API_KEY}", "ENDPOINT": ENDPOINT}
    for endpoint in put_endpoints:
        _template = put_template.copy()
        _template["endpoint_suffix"] = endpoint
        cases.append(_template)

    curl_strings = []
    for case in cases:
        if "png" in case["endpoint_suffix"]:
            name = "test_" + str(int(random.random()*1000000)) + ".png"
            curl_strings.append("curl -X {method} -H '{headers}' {ENDPOINT}{endpoint_suffix} -o ".format(**case) + name)
        else:
            curl_strings.append("curl -X {method} -H '{headers}' {ENDPOINT}{endpoint_suffix} | jq .".format(**case))
    return curl_strings

if __name__ == "__main__":
    print("#!/bin/bash\nset -e\n") # Bash script header, exit on error
    curl_strings = generate_curl_commands()
    for cs in curl_strings:
        print(cs)

    print("\n# Cleanup SQL commands:")
    for cmd in cleanup:
        print(f"echo {cmd}")
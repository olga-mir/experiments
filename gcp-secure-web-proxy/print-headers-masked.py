def request(flow):
    print("New request:")
    print(f"Method: {flow.request.method}")
    print(f"URL: {flow.request.pretty_url}")
    print("Headers:")
    for name, value in flow.request.headers.items():
        if name.lower() == 'authorization':
            # Assuming the header format is 'Bearer TOKEN'
            parts = value.split()
            if len(parts) == 2:
                token = parts[1]
                # Show only the first 5 and last 5 characters of the token
                if len(token) > 10:
                    masked_token = f"{token[:5]}...{token[-5:]}"
                else:
                    masked_token = token  # Token is too short to mask effectively
                print(f"{name}: {parts[0]} {masked_token}")
            else:
                print(f"{name}: {value}")  # Print original header if format is unexpected
        else:
            print(f"{name}: {value}")


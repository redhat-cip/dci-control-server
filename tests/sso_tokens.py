# Generate TOKEN using website like https://token.dev/
# Copy new public and private keys in tests/settings.py
_doc_access_token_user1 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": "dci",
  "sub": "3272474d-a083-4e37-9426-867aa6a46ed6",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "b774d7ea-2c32-44a7-91a8-1b7c8ff98706",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "user1@example.org",
  "username": "user1"
}
"""

ACCESS_TOKEN_USER1 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiMzI3MjQ3NGQtYTA4My00ZTM3LTk0MjYtODY3YWE2YTQ2ZWQ2IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYjc3NGQ3ZWEtMmMzMi00NGE3LTkxYTgtMWI3YzhmZjk4NzA2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJ1c2VyMUBleGFtcGxlLm9yZyIsInVzZXJuYW1lIjoidXNlcjEifQ.QC0RWsR6_UGzIpeMKlV60FodUsiqu9go4BfdT8jd85FcgHiMLJkCO_jhKtlfaMILImQSzcGjNOpBYZWHjdgo3IHVPLsP1rvknNtxSdjU8XQMzvfmjoT_ZUYeiRIcDU2YgJd0cN1AjUxxAuDYNEjS-L_TFW3KPyl9RUsMK0bb9GmxMG1JplWncfFeG9kd2-Fva0jdMvH4WPu5DNkYQ3ky3p5_OQVycUBncBYcM04Uz2Fj4WiBc9TqqIN4uzATj67AOfSpNsw6NCNOL2s3M5RtPQq2_ja24DcxESI48grKv_i5SEKSei9y83937ShbE45x1bT8dWceEvbajTnueqA24A"

_doc_access_token_user4 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": "dci",
  "sub": "3272474d-a083-4e37-9426-867aa6a46ed6",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "b774d7ea-2c32-44a7-91a8-1b7c8ff98706",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "user4@example.org",
  "username": "user4"
}
"""

ACCESS_TOKEN_USER4 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiMzI3MjQ3NGQtYTA4My00ZTM3LTk0MjYtODY3YWE2YTQ2ZWQ2IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYjc3NGQ3ZWEtMmMzMi00NGE3LTkxYTgtMWI3YzhmZjk4NzA2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJ1c2VyNEBleGFtcGxlLm9yZyIsInVzZXJuYW1lIjoidXNlcjQifQ.JyjuZncNs0Sxs-GvakxsXWQ01IeniIVY8Or6HQtSQd3GMUD7F9Ibocm-g7-sMqc1GfRvYA89g7Kj0L6mmoe3NpNObxoxP5HKabElnmkYuL7ocyjU7KhNpePV0dn6gE20jH8efWpIf0jLLCmdpcG3TPZZ532tCHLQcyjlfE5L_UzFBvHPrXJrr-SxixqauxTth0moZ7UOPx3Aj4YW8UD54AgK3soKmkOGXyeRVC2edp0iDMJ1tfxQqWifZyXhMUEXvoAp0slR7fXxa2WrYQALBAyJeTOu3F3qa4dIifux48Lo9KGe7ibuMnHVFSQ52JPgMe10CC_3NF7Ukz27sVDYrA"

_doc_access_token_rh_employee = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "9717d8b3-73d9-4b6e-be8f-fc9fe9a24454",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": "dci",
  "sub": "ddf4ce78-6682-4df2-bbbc-f2e61fe576e0",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "85ae77a0-87eb-4c5d-938e-90f251a2071e",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "redhat:employees",
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "rh_employee@redhat.com",
  "username": "rh_employee"
}
"""

ACCESS_TOKEN_RH_EMPLOYEE = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5NzE3ZDhiMy03M2Q5LTRiNmUtYmU4Zi1mYzlmZTlhMjQ0NTQiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiZGRmNGNlNzgtNjY4Mi00ZGYyLWJiYmMtZjJlNjFmZTU3NmUwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiODVhZTc3YTAtODdlYi00YzVkLTkzOGUtOTBmMjUxYTIwNzFlIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInJlZGhhdDplbXBsb3llZXMiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoicmhfZW1wbG95ZWVAcmVkaGF0LmNvbSIsInVzZXJuYW1lIjoicmhfZW1wbG95ZWUifQ.Uc4wOqmpLAlEpC6obFfsmPYkWiBsSBv8DwP9nqnZ5KRWgIG3B8lj3aiUbeKNOLgf5C0o0uJikK0l6_VOO_Djy20fOOkog6AVG7bNkQIN2mIj1-U7s-S9NizxGdDkcc7la-x79yR0jEk39TRw8nyPWREJ8rl5KL7_7NosrRaGXxPszHVWM9Dfr-YzlymOtp5vFwXeKY_iF-4MNOcnMi0dfGPoDyrtCPnfjZbVxlkIddHuNkyGmBQI6lNbCycrLl1oORvZADN4J118yzYznWzVWzFWwh5bnahZfbjfy2kIhnSiunqIb68ebq4FIExKAlTErxcRo3yCRPSRzCoZEv21pg"

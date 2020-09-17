_doc_access_token_user = """
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "uQxsQppsKoobFh3HNtkuWoRjFdu0cktF-Sy4eWE5xy4"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1518653829,
  "nbf": 0,
  "iat": 1518653529,
  "iss": "http://localhost:8180/auth/realms/dci-test",
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
  "email": "dci@distributed-ci.io",
  "username": "dci"
}
"""

ACCESS_TOKEN_USER = (
    "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ1UXh"
    "zUXBwc0tvb2JGaDNITnRrdVdvUmpGZHUwY2t0Ri1TeTRlV0U1eHk0In0.eyJqdGkiOiJkND"
    "g1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE1MTg2NTM4MjksI"
    "m5iZiI6MCwiaWF0IjoxNTE4NjUzNTI5LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAv"
    "YXV0aC9yZWFsbXMvZGNpLXRlc3QiLCJhdWQiOiJkY2kiLCJzdWIiOiIzMjcyNDc0ZC1hMDg"
    "zLTRlMzctOTQyNi04NjdhYTZhNDZlZDYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJkY2kiLC"
    "JhdXRoX3RpbWUiOjAsInNlc3Npb25fc3RhdGUiOiJiNzc0ZDdlYS0yYzMyLTQ0YTctOTFhO"
    "C0xYjdjOGZmOTg3MDYiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9s"
    "b2NhbGhvc3Q6ODAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsidW1hX2F1dGhvcml"
    "6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbm"
    "FnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19L"
    "CJlbWFpbCI6ImRjaUBkaXN0cmlidXRlZC1jaS5pbyIsInVzZXJuYW1lIjoiZGNpIn0.VxCn"
    "nbaDfolfv4k25zCZE2XTrPJ5zswtIBYrZXUcEe1G7r-WBQjPtcKTPbHwYVIUJgz6EiON3f7"
    "3mJWmw4VBl-c2KeU7dwSkYQ6sM7oX2n6T_N7qXuVEYc_ijOZpGbSW_C-b1Mj-yCTrSt_TjN"
    "1fIE43iUz2wSzNOpZFG27QPqDic9hV0WpCN-uz_dqK3FlTkA-e3V2gtj02CzWUpu22Ca2DC"
    "DtEZON14XqKpf0ddv33LkyuYkMtYDD9vn05TsxcJDaUrXdmvUDtH98gmtg07lK56quFFvP5"
    "jl7gMdqynl198x60q2PHrLMb72nMDcAxGzeCB4BMbN60mKGOum_Mzw"
)

_doc_access_token_rh_employee = """

{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "uQxsQppsKoobFh3HNtkuWoRjFdu0cktF-Sy4eWE5xy4"
}
{
  "jti": "9717d8b3-73d9-4b6e-be8f-fc9fe9a24454",
  "exp": 1518654295,
  "nbf": 0,
  "iat": 1518653995,
  "iss": "http://localhost:8180/auth/realms/dci-test",
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
  "email": "dci-rh@redhat.com",
  "username": "dci-rh"
}
"""

ACCESS_TOKEN_READ_ONLY_USER = (
    "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkI"
    "iA6"
    "ICJ1UXhzUXBwc0tvb2JGaDNITnRrdVdvUmpGZHUwY2t0Ri1TeTRlV0U1eHk0In0.eyJqdGk"
    "iOiI5NzE3ZDhiMy03M2Q5LTRiNmUtYmU4Zi1mYzlmZTlhMjQ0NTQiLCJleHAiOjE1MTg2NT"
    "QyOTUsIm5iZiI6MCwiaWF0IjoxNTE4NjUzOTk1LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0O"
    "jgxODAvYXV0aC9yZWFsbXMvZGNpLXRlc3QiLCJhdWQiOiJkY2kiLCJzdWIiOiJkZGY0Y2U3"
    "OC02NjgyLTRkZjItYmJiYy1mMmU2MWZlNTc2ZTAiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJ"
    "kY2kiLCJhdXRoX3RpbWUiOjAsInNlc3Npb25fc3RhdGUiOiI4NWFlNzdhMC04N2ViLTRjNW"
    "QtOTM4ZS05MGYyNTFhMjA3MWUiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0d"
    "HA6Ly9sb2NhbGhvc3Q6ODAwMCJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsicmVkaGF0"
    "OmVtcGxveWVlcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOns"
    "iYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LW"
    "xpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJkY2ktcmhAcmVkaGF0LmNvbSIsI"
    "nVzZXJuYW1lIjoiZGNpLXJoIn0.bFb_lbnLfBMJbidflrR2UQoYNUvyffP15GYEq30vj7JP"
    "1IsmxI_5tNi7-EqN78sazsT1g7MQG_Wq-HknvACb4ll-LpROQvxg8fopLZaxn9dRNZGyiZX"
    "92oJCPmNZHHwESyieEcvJ3UoAmX3nCo3jZVFhxuRwyd7iKkX8IQovXKQ-K-8Ju78NAeVEXV"
    "-U4Xy_ZmFncePPO7xlUAF5J5P7pLq1ciKa_MnuZeL5hkEO8AfXo2yYJ1DRij65H_H4V6jA2"
    "W0pi1o7eimFQR4oK_XgmX_u0dpJGf8GLFDkT8Saxj7zJeDtgNJqkE8DAB2m8XFdd2KYKNe7"
    "FmJpCOrSfYe1Ow"
)

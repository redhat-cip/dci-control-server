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
  "email": "dci@distributed-ci.io",
  "username": "dci"
}
"""

ACCESS_TOKEN_USER = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InVReHNRcHBzS29vYkZoM0hOdGt1V29SakZkdTBja3RGLVN5NGVXRTV4eTQifQ.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE1MTg2NTM4MjksIm5iZiI6MCwiaWF0IjoxNTE4NjUzNTI5LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiMzI3MjQ3NGQtYTA4My00ZTM3LTk0MjYtODY3YWE2YTQ2ZWQ2IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYjc3NGQ3ZWEtMmMzMi00NGE3LTkxYTgtMWI3YzhmZjk4NzA2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJkY2lAZGlzdHJpYnV0ZWQtY2kuaW8iLCJ1c2VybmFtZSI6ImRjaSJ9.uC3dVVYgdfaMw7oB4dOZvvF4pETKCqumN4c9uK_WYk37Pz_S_e5gnLJGD_uhpsUqW4YiozSzKTn6acCRBjjffwKTtCinO7uThjriqkDHUiYFWmxu6J24Yk4C8TJktaBYlU-uN661N7BfYknxdN9sFNSH5SpVgDw4DoQYW462taDk4bDOhhTv_MWX-f1gac2bn-TUVc9_pad50T_vyaKD0lcDuB6fe28nkk1m1pToonze1GCuJEFcnI8m1UEl48oM4k8qWXLYAT5ngQQ8_XMO8AlnMfwH26wXeU1bPWXk1STPmyCfD6IplV_dQmVekGfzf3gsPZ1L-Oc2uRu-FiiELA"

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
  "email": "dci-rh@redhat.com",
  "username": "dci-rh"
}
"""

ACCESS_TOKEN_READ_ONLY_USER = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InVReHNRcHBzS29vYkZoM0hOdGt1V29SakZkdTBja3RGLVN5NGVXRTV4eTQifQ.eyJqdGkiOiI5NzE3ZDhiMy03M2Q5LTRiNmUtYmU4Zi1mYzlmZTlhMjQ0NTQiLCJleHAiOjE1MTg2NTQyOTUsIm5iZiI6MCwiaWF0IjoxNTE4NjUzOTk1LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiZGRmNGNlNzgtNjY4Mi00ZGYyLWJiYmMtZjJlNjFmZTU3NmUwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiODVhZTc3YTAtODdlYi00YzVkLTkzOGUtOTBmMjUxYTIwNzFlIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInJlZGhhdDplbXBsb3llZXMiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoiZGNpLXJoQHJlZGhhdC5jb20iLCJ1c2VybmFtZSI6ImRjaS1yaCJ9.mO69Kp2PzI3ul-Ruf3uXtX1ysjxZczUaJnsyWdnJFyvbn0VA9s1LwVg0mfcMlpm_gETQ-pt1-eAvj-RPF8h-CKNaiTzNFcM1J9c-1v2L_2Z5mBpA56_z8apI7qBThaUYoiuYn2emNIgbv-qZYz_YPgoApVUMvJhQhJ1U2aHcD7t0sV52POu79M0h32W1A089iYlFhfdM5SG9gytIKOfdXSaksHMte4IwMz34PNgGkduhtLO4VhdadRAve1FeyFxOaTWTQcn2c_91nRzaTGvzUlbnBk3eFxH7Fgvwb4HWs3zoifbdqfJAfuoUSHNwOzW73wiNYk75GRkBrMgv4PmN3A"

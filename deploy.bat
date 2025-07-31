aws s3 cp --recursive aws/ s3://twitter-backup4/ --profile tmg
aws cloudfront create-invalidation --distribution-id E1RHMO44DO8QS9 --paths "/*" --profile tmg > NUL
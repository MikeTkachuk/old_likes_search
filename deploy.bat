aws s3 cp ./aws/index/* s3://twitter-backup4/
aws cloudfront create-invalidation --distribution-id E1RHMO44DO8QS9 --paths "/*" --profile tmg
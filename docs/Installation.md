You need the AI-Core Package

For that you need to run `aws configure sso` and `aws sso login` first and then add the correct codeartifact.

```bash
export UV_INDEX_INFORM_AI_USERNAME="aws"
export UV_INDEX_INFORM_AI_PASSWORD="$(
  aws codeartifact get-authorization-token \
    --domain inform-ai \
    --domain-owner 637423203277 \
    --query authorizationToken \
    --output text
)"
```

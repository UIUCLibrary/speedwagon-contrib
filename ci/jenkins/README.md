# README

## Testing packages with other versions of Python
To use the Testing Packages stages in Jenkins pipeline with other versions of Python, create a config file in Jenkins 
with the fileId "python_config". 
The file should contain a key "supported_python_versions" with a list of python versions to test against. 

For example:

```json

{
  "supported_python_versions": [
    "3.8",
    "3.9",
    "3.10",
    "3.11"
  ]
}
```
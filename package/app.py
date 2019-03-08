from chalice import Chalice
from chalicelib import awsAuditor

app = Chalice(app_name='package')

@app.lambda_function()
def lambda_handler(event, context):
    awsAuditor.main()

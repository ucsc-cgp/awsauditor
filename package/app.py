from chalice import Chalice
from chalicelib import awsAuditor

app = Chalice(app_name='package')

@app.lambda_function()
def lambda_handler(event, context):
    awsAuditor.main()

# Option to set up the lambda to run on a schedule specified in cron format
# This example will run at 8:30 pm UTC every day
# @app.schedule('cron(30, 20, *, *, ?, *)')
# def lambda_handler(event):
#     awsAuditor.main()


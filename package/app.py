from chalice import Chalice
from chalicelib import awsAuditor

app = Chalice(app_name='package')

@app.lambda_function()
def lambda_handler(event, context):
    awsAuditor.main()


# @app.schedule('cron(30, 20, *, *, ?, *)')
# def lambda_handler(event):
#     awsAuditor.main()


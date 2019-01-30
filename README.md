# awsauditor
A tool for interrogating AWS billing data using the Cost Explorer API. It makes customized reports in text and graphic form, and emails them out to people. awsauditor is intended for use with Amazon CloudWatch, so it can be automated to run daily. There is currently no command line tool to use awsauditor.

## Usage
We are using Chalice to create lambdas for awsauditor so that its dependencies, matplotlib and numpy, can be included easily in a package compatible with AWS Lambda.

Download the entire package directory.
Install chalice, if not already done so:

`pip install chalice`

Edit .chalice/config.json to include ARN for the IAM role for the lambda to be created.
This role must include permissions to use AWS Organizations and AWS Cost Explorer operations.

If you want awsauditor to run on a schedule, in app.py, replace the code under `@app.lambda_function` with that under `@app.schedule` (commented out by default). The given example will run at 10 AM every day. For more information about scheduling, see https://chalice.readthedocs.io/en/latest/topics/events.html.

Create the lambda:

`chalice deploy`


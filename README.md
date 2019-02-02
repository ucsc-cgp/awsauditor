# awsauditor
A tool for interrogating AWS billing data using the Cost Explorer API. It makes customized reports in text and graphic form, and emails them out to people. awsauditor is intended for use in an AWS Lambda so it can be automated to run daily. There is currently no command line tool to use awsauditor.

## Usage
We are using Chalice to create lambdas for awsauditor so that its dependencies, matplotlib and numpy, can be included easily in a package compatible with AWS Lambda.

Download the entire package directory.
Install chalice, if not already done so:

`pip install chalice`

Edit .chalice/config.json to include ARN for the IAM role for the lambda to be created.
This role must include permissions to use AWS Organizations and AWS Cost Explorer operations.

If you want awsauditor to run on a schedule, in app.py, replace the code under `@app.lambda_function` with that under `@app.schedule` (commented out by default). The given example will run at 10 AM every day. For more information about scheduling, see https://chalice.readthedocs.io/en/latest/topics/events.html.

From within the package directory, create the lambda:

`chalice deploy`

## Configuration
To configure awsauditor to send emails, edit chalicelib/reportGenerator.py to include your email and password.
On line 513, edit to include your email address:

`sender = "you@email.com"`

On line 530, edit to include your password:

`s.login(sender, "y0urp@ssword")`

To set who receives emails, edit chalicelib/awsAuditor.py, which contains a dictionary called `managers` and a list called `individuals`.
The dictionary maps email addresses to lists of account names. People who have emails in this dictionary will get a report for each account mapped to them. The list contains email addresses for which to send individual reports. People who have emails in this list will get a report showing only their expenses.

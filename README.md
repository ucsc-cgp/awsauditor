# awsauditor
A tool for interrogating AWS billing data using the Cost Explorer API. It makes customized reports in text and graphic form, and emails them out to people. awsauditor is intended for use with Amazon CloudWatch, so it can be automated to run daily. There is currently no command line tool to use awsauditor.

## Usage
Download package.zip, which contains all the other files in the repo plus their dependencies, matplotlib and numpy.
Install the AWS command line interface, if you haven't already:

`pip install aws`

Make a new lambda:

`aws lambda create-function --function-name sendEmails --runtime python3.7 --role arn:aws:iam::862902209576:role/lambda_basic_execution --handler awsAuditor.main --zip-file fileb://package.zip`

Make a new CloudWatch event:

`aws events put-rule --name emailSender --schedule-expression cron(0, 10, *, *, ?, *)`

Set the event to trigger the lambda (use the arn corresponding to your lambda):

`aws events put-targets --rule emailSender --targets "Id=1","Arn=arn:aws:lambda:us-west-2:0000000000000000:function:reportTest"`

Email credentials and recipients are hard-coded, and need to be modified.

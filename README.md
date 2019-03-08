# awsauditor
A tool for interrogating AWS billing data using the Cost Explorer API. `awsauditor` is intended for use as an AWS Lambda so it can be automated to run daily.

Emails are sent out to managers and individual users that contain text and graphical reports breaking down MTD AWS expenditures.
Emails sent to managers detail how much each user spent on the accounts they are responsible for.
Emails sent to individuals summarize an individual's expenditures across accounts and services.


## Configuration

`awsauditor` gets all of its configuration information from a .json file that is stored in an AWS S3 bucket.
Change line 38 and 39 to specify the name of bucket and .json, respectively.

Lets break down an example config.json:

    {
        
        "managers": {"manager1@email.com":["Account1", "Account3"], "manager2@email.com":["Account2", "Account4"]},
        
        "users": ["dev1@email.com", "dev2@email.com"],
        
        "secret_name": "emailsecret"
    }

`managers`: This dictionary specifies email address and the accounts they will receive reports for.

`users`: This list specifies email addresses which will receive reports for their account activity across AWS accounts.

`secret_name`: `awsauditor` sends out emails from an email address who's information is stored in the AWS Secret specified
by this secret name. See https://aws.amazon.com/secrets-manager/getting-started/ for more information about AWS Secrets.

The config.json needs to have this structure. 

Note that all of the quotation marks are double quotes. This is important. 

## Initial Deployment
We are using Chalice to create lambdas for `awsauditor` so that its dependencies, matplotlib and numpy, can be included easily in a package compatible with AWS Lambda.

Download the entire package directory.
Install chalice, if not already done so:

`pip install chalice`

Edit .chalice/config.json to include ARN for the IAM role for the lambda to be created.
This role must include permissions to use AWS Organizations and AWS Cost Explorer operations.

From within the package directory, create the lambda:

`chalice deploy`


## Automation
You can trigger the lambda with an AWS CloudWatch Event. See https://aws.amazon.com/cloudwatch/ for more info about CloudWatch Events.

Note that after redeploying the lambda, you must readd this event to the lambda again via the lambda management console.
There is potentially another way to automatically configure this, we just haven't gotten the chance to set it up yet:
see https://chalice.readthedocs.io/en/latest/topics/events.html.


## Maintainiance
After making any changes to the code in here, ie: changing bucket or config file names, the lambda must be redeployed

From `/path/to/awsauditor/package` run:

`chalice deploy`
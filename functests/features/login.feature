Feature: login to splunk
    If splunk is up and running, a user should be able to login

    Scenario: Login with credentials
        Given splunk container is up and running
        Then login to splunk
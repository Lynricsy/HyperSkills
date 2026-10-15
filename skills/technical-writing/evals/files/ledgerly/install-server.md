# Install the Ledgerly server on Windows

This guide gets a Ledgerly server running on one Windows Server 2022 machine. It takes
about 15 minutes.

## Before you start

You need an administrator account and the licence key from your welcome e-mail.

![](img/welcome-email.png)

## 1. Run the installer

Download `LedgerlySetup.msi` and double-click it. When the installer asks for the
installation type, pick the option shown below.

![](img/installer-type.png)

## 2. Configure the service

On the **Service** page, fill in the fields exactly as in this screenshot, then click
**Next**. Getting this page wrong is the most common cause of support tickets.

![](img/service-page.png)

## 3. Edit the configuration file

Open `C:\ProgramData\Ledgerly\ledgerly.conf` in Notepad and make it look like this:

![](img/ledgerly-conf.png)

## 4. Check that it works

Open the address from step 2 in a browser. You should see this:

![](img/first-login.png)

If you see something else, check the troubleshooting flowchart:

![Troubleshooting](img/troubleshooting-flowchart.png)

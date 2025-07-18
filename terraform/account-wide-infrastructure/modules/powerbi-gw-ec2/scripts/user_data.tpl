

<powershell>
Install-WindowsFeature -name Web-Server -IncludeManagementTools

$instanceId   = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/instance-id -UseBasicParsing).content
$instanceAZ   = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/placement/availability-zone -UseBasicParsing).content
$pubHostName  = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/public-hostname -UseBasicParsing).content
$pubIPv4      = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/public-ipv4 -UseBasicParsing).content
$privHostName = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/local-hostname -UseBasicParsing).content
$privIPv4     = (Invoke-WebRequest -Uri  http://169.254.169.254/latest/meta-data/local-ipv4 -UseBasicParsing).content

New-Item -Path C:\inetpub\wwwroot\index.html -ItemType File -Force
Add-Content -Path C:\inetpub\wwwroot\index.html "<font face = "Verdana" size = "5">"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center><h1>AWS Windows VM Deployed with Terraform</h1></center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>EC2 Instance Metadata</b> </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>Instance ID:</b> $instanceId </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>AWS Availablity Zone:</b> $instanceAZ </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>Public Hostname:</b> $pubHostName </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>Public IPv4:</b> $pubIPv4 </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>Private Hostname:</b> $privHostName </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "<center> <b>Private IPv4:</b> $privIPv4 </center>"
Add-Content -Path C:\inetpub\wwwroot\index.html "</font>"

</powershell>

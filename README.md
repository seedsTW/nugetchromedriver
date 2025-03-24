# nugetchromedriver
This program could help you to download Chromedriver from nuget automatically.

A few years ago, we wrote a web‑scraping program for a client that could automatically update ChromeDriver. However, once the client put a firewall in place, issues began to occur.

The purpose of this script is to go directly to NuGet and automatically download the matching ChromeDriver version. We match google version with chromedriver with (major.minor.build, e.g. “134.0.6998”). Since compatibility between ChromeDriver and Chrome isn’t determined solely by the major version number—it requires matching the first three segments (major.minor.build). According to the official guidance, ChromeDriver and Chrome must share the same first three version segments to guarantee full compatibility; the patch segment may differ.

However, if you do not want download or update so frequentlly, you could change the code freely to meet your needs.

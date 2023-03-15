<div id="top"></div>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" height="80">
  </a>

  <h3 align="center">SNA Autometron</h3>

  <p align="center">
    Identify Peer IP addresses and Add to the Hostgroup of Your Choice!
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Report Bug</a>
    ·
    <a href="https://github.com/othneildrew/Best-README-Template/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project


Identifying peer hosts on the internet may be integral to your optimal security posture.  Unfortunately it can be difficult to associate IP addresses with domains.

This project hopes to help manage that difficulty by monitoring unknown peers on the web and using data from Shodan to correlate to a particular domain.  This way you can more easily identify internet based peers your internal hosts are communicating with.

This script will execute flow queries searching for flows from a destingated internal host group searching for unidentified hosts on the web. These peers will be evaluated against Shodan to try and associate a domain with the peer IP addresses.

Once you have identified the peer domains - you can choose to automatically add hosts associated with your target domain(s) to a specified Outside hostrgroup.  In addition, an Excel spreadsheet will be generated identifying the IP addresses and associated domain name(s) of other peer IP's that do not match your given criteria. This can allow you to investigate these connections and drop them in host groups as needed.



<p align="right">(<a href="#top">back to top</a>)</p>



### Built With

* [Python](https://python.org/)

#### APIs Used
* [Shodan API Reference](https://developer.shodan.io/api)
* [Cisco Secure Network Analytics API Reference](https://developer.cisco.com/docs/stealthwatch/enterprise/)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.
<!--
### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```
-->

### Installation

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Clone the repo
   ```sh
   git clone https://github.com/gobblegoob/SNA-Automatron.git
   ```
2. Install dependencies from requirements.txt
   ```sh
   pip install -r requirements.txt
   ```
3. Obtain an API key for Shodan.  This can be done by creating a free account at https://www.shodan.io

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

The application needs to know the following bits of information to run.

1. SMC URL and credentials 
2. A Secure Network Analytics Query you wish to run - It helps to create this in your SMC so you can hone your report
3. Shodan API key - requires a free Shodan account
4. A destination Host Group you want to populate with identified IP addresses - It helps to configure a nested Host Group as a destination which will only be updated dynamically
6. A domain name you want to search for (IE: ring.com)

<p>Before you set up the script - you need to design a Flow Query to identify the target peer IP addresses you want to query Shodan for.  The results of this query will be looked up in Shodan where domain and certificates CN/SANs will be checked to see if they match your targeted domain.  Design and hone your Flow Query in the SNA Flow Query screen.  Once you have designed your query - you can easily transfer the query parameters to the sna.json file.  </p>

<p>Example query:</p> 
<img src="images/flowsearch.PNG" alt="Example Flow Query">

### To set up:
 - Add your API key to shodan.json
 - Add the following data to sna.json
 SMC hostname/IP and credentials
 Source/Subject Hostgroups to include and exclude from your query
 Destination/Peer hostgroups to include and exclude from your query
 
 ### Optional:
 You can add values for the following global variables to make it easier to run the application.  These variables are kept in [FILE]
 1. <br>MY_DOMAIN</br> - This is the domain you want to search
 2. <br>MY_TAG_TO_UPDATE</br> - This is the destination host group - all IP's that match your search criteria will be automatically added to this host group
 3. <br>CERT_STR - Sometimes a domain won't be listed in Shodan - this is a regex string you can add to match part of the CN or SAN fields in a site certificate as captured by Shodan.

### Scheduling:
It may be necessary depending on the domain that you repeat this task.  You can schedule a cron job in linux to execute the script. To run the script at 11pm each day and output a log file for tracking, add the folloiwng to your crontab file:
```
00 23 * * * cd /[path/to/file] && python snatesting.py >> tagupdate.log 
```

- **[Cron Job: A Comprehensive Guide for Beginners 2023](https://www.hostinger.com/tutorials/cron-job)**
- **[Crontab Generator](https://crontab-generator.org/)**

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Allow for multiple destination hostgroups
- [ ] Easier user interaction
- [ ] Simultaneous search for multiple target domains
- [x] If no data is found on Shodan for a particular IP address - add that info to the Other Domains Report for further review


See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/gobblegoob/SNA-Automatron](https://github.com/gobblegoob/SNA-Automatron)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments


Thank yous

* [denapom11 SNA Examples](https://github.com/CiscoDevNet/stealthwatch-enterprise-sample-scripts)
* [othneildrew Best README Template](https://github.com/othneildrew/Best-README-Template)


<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/gobblegoob/SNA-Automatron/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/gobblegoob/SNA-Automatron/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/gobblegoob/SNA-Automatron/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/
[product-screenshot]: images/screenshot.png

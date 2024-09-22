# PyAniTrack
[![Build Status](https://github.com/GreenMachine582/pyanitrack/actions/workflows/project_tests.yml/badge.svg?branch=main)](https://github.com/GreenMachine582/pyanitrack/actions/workflows/project_tests.yml)
![Python version](https://img.shields.io/badge/python-3.7-blue.svg)
[![GitHub commits](https://img.shields.io/github/commits-since/GreenMachine582/pyanitrack/latest.svg)](https://github.com/GreenMachine582/pyanitrack/commits/main)

## Table of Contents
- [Introduction](#introduction)
- [Current Features](#current-features)
  - [1. Database Management with Python](#1-database-management-with-python)
  - [2. API Integration for Manga and Anime Information](#2-api-integration-for-manga-and-anime-information)
  - [3. Comprehensive Unit Testing](#3-comprehensive-unit-testing)
- [Proposed Features and Future Developments](#proposed-features-and-future-developments)
  - [1. Pygame User Interface (UI)](#1-pygame-user-interface-ui)
  - [2. History Tracking](#2-history-tracking)
  - [3. Review System](#3-review-system)
  - [4. User Watchlist Management](#4-user-watchlist-management)
  - [5. Enhanced Search and Filtering](#5-enhanced-search-and-filtering)
  - [6. Graphing History, Genres, and Activity](#6-graphing-history-genres-and-activity)
  - [7. Recommendation System](#7-recommendation-system)
  - [8. User Authentication and Profiles](#8-user-authentication-and-profiles)
  - [9. Cross-Platform Compatibility](#9-cross-platform-compatibility)
  - [10. Social Sharing and Community Features](#10-social-sharing-and-community-features)
  - [11. Cloud Sync and Backup](#11-cloud-sync-and-backup)
  - [12. Mobile Application](#12-mobile-application)
- [Testing](#testing)
- [License](#license)

---

## Introduction
PyAniTrack is a comprehensive tool designed to help users manage their anime and manga collections. It integrates with 
the Jikan API to fetch up-to-date information and provides a user-friendly interface built with Pygame to track 
watchlists, history, and reviews. This document outlines the current features and proposes potential future 
developments for the project.

## Current Features

### 1. Database Management with Python
PyAniTrack uses a Python-based database management system that allows users to create, update, and modify the 
underlying database schema. The database tracks user information such as watchlists, history, and reviews.
**Database Creation and Updates**
* **Versioned Migration:** The database schema and data are version-controlled, with updates applied through SQL and 
Python scripts. 
  * The `v#_create_schema.sql` and `v#_create_popupate.py` files define the base schema for new versions.
  * The `v#_to_v#_upgrade_schema.sql` and `v#_to_v#_upgrade_population.py` scripts handle incremental upgrades, 
ensuring that data is migrated smoothly.
* **Migration Process:** During updates, rows are processed one at a time, ensuring complete migration and data 
integrity.

### 2. API Integration for Manga and Anime Information
PyAniTrack integrates with the Jikan API to fetch detailed anime information. This includes:
* **Multi-page Data Fetching:** The application makes multiple requests to retrieve data from all pages when querying 
large results.
* **Filtered Results:** Results are processed to filter out unrelated titles using string comparison techniques,
ensuring only relevant data is included.
The API provides data such as synopses, genres, episode counts, release dates, and more, ensuring users have access to 
up-to-date information.

### 3. Comprehensive Unit Testing
PyAniTrack includes a suite of unit tests that ensure the reliability of the application's key features such as 
database creation, updates, and API integration. This helps verify the system’s stability and integrity across various 
features.
#### Running Unit Tests
To execute the test suite, run the following command from the project root:
```bash
python -m unittest discover -s tests
```
**Tests cover:**
* Database schema creation and migrations

## Proposed Features and Future Developments

### 1. Pygame User Interface (UI)
The UI is built using Pygame, providing an interactive and visually appealing experience. Users can navigate through 
different sections of the application, view detailed information about manga and anime titles, and manage their 
watchlist and history in an intuitive manner.

### 2. History Tracking
The application automatically tracks and records the user's viewing or reading history. This feature allows users to 
easily revisit previously watched or read titles and see their progression over time.

### 3. Review System
Users can leave reviews for the anime and manga titles they have watched or read. The review system supports rating 
titles on a numerical scale and adding written comments. This feature helps users document their thoughts and opinions 
on various titles.

### 4. User Watchlist Management
Users can create and manage a personalised watchlist, adding titles they plan to watch or read. The watchlist includes 
options to mark titles as completed, in progress, or on hold. This feature helps users keep track of their anime and 
manga consumption.

### 5. Enhanced Search and Filtering
Implement advanced search and filtering capabilities to allow users to find specific titles based on criteria such as 
genre, release year, ratings, and more. This feature would improve the user experience by making it easier to discover 
new anime and manga.

### 6. Graphing History, Genres, and Activity
Introduce data visualisation features that allow users to gain insights into their anime and manga consumption patterns 
through interactive graphs and charts.

### 7. Recommendation System
Develop a recommendation system that suggests anime and manga titles based on the user's watchlist, history, and 
ratings. This system could use machine learning algorithms to analyze user preferences and recommend titles that align 
with their interests.

### 8. User Authentication and Profiles
Introduce user authentication to allow multiple users to maintain separate profiles within the application. This would 
enable each user to have their personalized watchlist, history, and reviews, enhancing the application's usability for 
households or shared environments.

### 9. Cross-Platform Compatibility
Extend the application’s compatibility to support multiple platforms, including Windows, macOS, and Linux. This would 
increase the application's accessibility and ensure a consistent experience regardless of the operating system.

### 10. Social Sharing and Community Features
Incorporate social features that allow users to share their watchlists, reviews, and ratings with friends. This could 
include integration with social media platforms or the creation of a community space within the application where users 
can discuss their favorite titles.

### 11. Cloud Sync and Backup
Add cloud synchronisation and backup functionality, allowing users to save their data in the cloud and access it from 
multiple devices. This feature would ensure that user data is secure and accessible from anywhere.

### 12. Mobile Application
Develop a mobile version of the application for iOS and Android devices. A mobile app would provide users with the 
convenience of managing their watchlists and history on the go, further enhancing the application's reach and 
usability.


## Testing
PyAniTrack includes a comprehensive suite of unit tests to ensure the reliability and stability of its features. Tests cover various aspects of the core functionality.

### Running Tests
To run the tests, navigate to the project root directory and execute the following command:

```bash
python -m unittest discover -s tests
```

## License
PyAniTrack is licensed under the MIT License, see [LICENSE](LICENSE) for more information.
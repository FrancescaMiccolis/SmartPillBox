# Smart Pill Box 


Smart Pill Box is an IoT device with a smart scale that provides help to people to properly take their medicaments. With an acoustic alarm and a LED, our scale draws patients' attention to avoid them to forget their pills. The service also provides some statistics to help the doctor to predict therapies' effectiveness. 

There are different actors in the sistem: 
- Catalog: management of devices, patients, settings, Publisher of Alarm messages 
- Dashboard: Publisher of therapies management made by the doctor. The Catalog is a Subscriber to its topic.
- Data Analyser: post-processing tool to calculate and update statistics for each patient. It POSTs updated stats on Thingspeak 
- Scale: Arduino device with weight sensors, LED, acoustic alarm; customized and personal device 
- Telegram: bot service to send alerts to the user and provide information about therapies and statistics
- WeightControl: service that manages weight and time inputs from Scale and POSTs results on ThingSpeak. Responsible also for missed assumption alarms activation

The doctor adds therapy information on his Dashboard and provides what's needed to his patient. A Telegram Bot is available to get a message when the prescribed assumption time comes. During the therapy, informations about weight and time accuracy are collected. Catalog is exposed by ngrok tunnel to ensure a safe communication channel. A Data Analyser provides statistics about each therapy adherence to the doctor.
Data Analyser stats:
* % dose=ok & time=ok
* % dose=ok & time!=ok
* % dose!=ok & time=ok
* % dose!=ok & time!=ok
* Streak: #max number of consecutive days with correct assumption in terms of both time and dose from the beginning of the therapy

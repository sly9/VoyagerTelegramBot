# VoyagerTelegramBot
by Liuyi Sun ([AstroBin](https://www.astrobin.com/users/liuyisun/)) and Kun Wang ([AstroBin](https://www.astrobin.com/users/bigpizza/))

Last updates: 12/11/2021

> We just released `v0.1.0` for Windows users! 🎉 Download it [here](https://github.com/sly9/VoyagerTelegramBot/releases/tag/V0.1.0)!

## Introduction
`VoyagerTelegramBot` is a lightweight client of Voyager Application Server.
Unlike the official [Web Dashboard](https://www.starkeeper.it/wdashinfo/),
`VoyagerTelegramBot` focuses on generating statistical charts and forwarding necessary messages
to [Telegram](https://telegram.org/).

With `VoyagerTelegramBot`, you don't need to keep a dashboard open to monitor the imaging session
for sub-images, system status, and critical warning and errors.  

## Features
- Configurable for types of images and messages
- Critical message forwarding

![Messages are forwared to Telegram clients](images/forwarded_messages_sample.png)
- Imaging session statistics per sequence

![Chat Sample with HFD plot, exposure time chat, and guiding error chat](images/target_report_sample.jpg)


## A Guide for Everyone

> We have prepared an application for everyone using Microsoft Windows (64bit),
> please go to our [release](https://github.com/sly9/VoyagerTelegramBot/releases) page to download it.

Before following this guide, please make sure the application server is enabled on your Voyager. (***important***)

1. Create a Telegram account; ([check here](https://telegram.org/))
2. Create a bot for the `VoyagerTelegramBot`; 
   ([check here](https://forum.starkeeper.it/t/send-free-custom-telephone-notifications-to-your-telegram-from-voyager/1889),
   under `Send Telegram` part)
   > **KEEP YOUR BOT TOKEN SECURE !!!**
3. Please make your bot an administrator of the group(after adding it to the group), so that it can pin message and update graph. 
      1. Instructions for telegram desktop app: 
         1. Goto your group chat in telegram, click '...'
         2. click 'view group info'
         3. click '...' of the group info pop-up
         4. click 'Manage Group'
         5. click 'Administrators'
         6. search for your bot, and add and save
      2. Instructions for telegram on iPhone (Android should have similar exp?)
         1. Goto your group chat in telegram, and tap the group name on the top
         2. Tap 'Edit' on top right
         3. Tap Administrators
         4. Tap 'Add Admin'
         5. Choose your bot
         6. save and exit
4. Download the latest version of `VoyagerTelegramBot` from [release](https://github.com/sly9/VoyagerTelegramBot/releases).
5. Double click the downloaded file, and follow the prompt.

If everything goes well, you should the main window of `VoyagerTelegramBot`.
![VoyagerTelegramBot_Main_Window](images/main_window.png)


## Full Installation Guide

> If you are confident with your skill of playing with python, or you are using Mac OS / Linux, please follow this full installation guide.

To deploy / use the `VoyagerTelegramBot` on your system, there are some basic requirements:

For the computer running Voyager application
- Voyager itself has been installed and configured.
- All necessary drivers and software packages are installed and configured.
- The application server is enabled on your Voyager.

For the computer running `VoyagerTelegramBot`
- python 3.7 or higher environments
- Able to connect to your Voyager Application Server
- Can be and can be not the same computer running Voyager application.

Currently, we only provide a general installation steps which may require some *geek* skills.
1. Prepare your stuffs
   1. Install python 3.7 or later environments;
   2. (*Optional*) Register for a Telegram account and install the app on your phone / tablet / computer ([check here](https://telegram.org/));
   3. Create a new Telegram bot and chat with your Telegram account;
   
      We are trying to write a guide, but before it's done, a quick guide can be found
      [here](https://forum.starkeeper.it/t/send-free-custom-telephone-notifications-to-your-telegram-from-voyager/1889),
      under `Send Telegram` part.
      > **KEEP YOUR BOT TOKEN SECURE**
   
   4. Please make your bot an administrator of the group(after adding it to the group), so that it can pin message and update graph. 
      1. Instructions for telegram desktop app: 
         1. Goto your group chat in telegram, click '...'
         2. click 'view group info'
         3. click '...' of the group info pop-up
         4. click 'Manage Group'
         5. click 'Administrators'
         6. search for your bot, and add and save
      2. Instructions for telegram on iPhone (Android should have similar exp?)
         1. Goto your group chat in telegram, and tap the group name on the top
         2. Tap 'Edit' on top right
         3. Tap Administrators
         4. Tap 'Add Admin'
         5. Choose your bot
         6. save and exit
2. Install package dependence for `VoyagerTelegramBot`;
   
   ```Shell
   pip3 install -r requirements.txt
   ```
3. Duplicate `config.yml.example` and rename it to `config.xml`.
For more information, please refer to [Configurations](https://github.com/sly9/VoyagerTelegramBot#configurations) session;
4. Launch the bot

   ```Shell
   python bot.py
   ```

## Configurations
The default and personalized configuration file () are both plain text,
you can open and edit it with any text editor (notepad, sublimetext, notepad++, just named a few).

Details of each configuration items are explained below.
```YAML
version: 0.5
```
Just the version number of our `VoyagerTelegramBot`, no need to touch it.
### Sequence Statistics
```YAML
sequence_stats_config:
  types: [ HFDPlot, ExposurePlot, GuidePlot ]
  hfd_plot_max_shots_count: -1
  guiding_error_plot:
    max_shots_count: -1
    unit: PIXEL
    scale: 1.21
  filter_styles:
    Ha:
      marker: +
      color: '#E53935'
    SII:
      marker: v
      color: '#B71C1C'
    OIII:
      marker: o
      color: '#3F51B5'
    L:
      marker: +
      color: '#9E9E9E'
    R:
      marker: +
      color: '#F44336'
    G:
      marker: +
      color: '#4CAF50'
    B:
      marker: +
      color: '#2196F3'
```
Current version supports 3 `types` of charts including
- *HFDPlot* contains HFD and StarIndex values
- *ExposurePlot* summarizes total exposure time per channel / filter
- *GuidePlot* plots all guiding errors as well as some basic statistics

Remove any of them if you don't want to receive the results.

The `filter_styles` defines the colors in chart for each type of filters, you could leave them as default.

### Messages
```YAML
text_message_config:
  send_image_msgs: 1  # Send jpeg images to chats
  allowed_log_types: [ WARNING, CRITICAL, TITLE, EMERGENCY ]
```
```YAML
send_image_msgs: 1  # Send jpeg images to chats
```
If `send_image_msgs` is set to `0`, previews of images will not be included in messages.
But the charts will not be affected.
### Software
```YAML
voyager_setting:
  domain: <voyager_url>  # Domain or IP for remote Voyager Server
  port: <voyager_port>  # port of remote Voyager Server
  username: <user_name>
  password: <password>
```
Information of the Voyager application server
```YAML
telegram_setting:
  bot_token: <telegram_token>
  chat_id: <chat_id>
```
`bot_token` can be found when creating new bot, and `chat_id` indicates where the messages will be sent to.
### Miscellaneous
```YAML
exposure_limit: 30
```
If the exposure time of an image is less than `exposure_limit`,
the image and corresponding messages are ignored, we use it to eliminate images for focusing.
```YAML
ignored_events: [ Polling, VikingManaged, RemoteActionResult, Signal, NewFITReady ]
```
Certain types of messages we received from Voyager application server are ignored.
```YAML
timezone: America/Los_Angeles
```
`timezone` is defined with location of your telescope. Eligible values are available [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
```YAML
should_dump_log: True
```
It's a setting for debug. If `True`, all messages received will be saved in a log file.
```YAML
monitor_battery: False
```
If you are using our `VoyagerTelegramBot` on a laptop, and wish to monitoring if the AC is connected and the battery level. Set this opition to `True`. The battery info is acquired by [`psutil`](https://github.com/giampaolo/psutil).
```YAML
debugging: False
allow_auto_reconnect: True
```
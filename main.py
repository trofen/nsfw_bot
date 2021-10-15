import telebot
import os
import requests
import av
from PIL import Image
from nsfw import classify
from io import BytesIO

#max probability rate for message delete
NSFW_MAX = 0.7
SEQ_SCANS = 5
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

me = bot.get_me()

@bot.message_handler(commands=['start', 'help'])
def handleWelcome(message):
	bot.reply_to(message, "Hi! I can rate content NSFW probability and delete this content from your groups!")
    
@bot.message_handler(content_types= ["photo"])
def handlePhoto(message):
    best_ps = message.photo[0]
    for ps in message.photo:
        if ps.file_size > best_ps.file_size:
            best_ps = ps
    handleStatic(message, best_ps.file_id)

@bot.message_handler(content_types= ["sticker"])
def handleSticker(message):
    handleStatic(message, message.sticker.file_id)
    
@bot.message_handler(content_types= ["animation"])
def handleAnimation(message):
    handleSequence(message, message.animation.file_id)
        
@bot.message_handler(content_types= ["video"])
def handleVideo(message):
    handleSequence(message, message.video.file_id)
    
@bot.message_handler(content_types= ["video_note"])
def handleVideoNote(message):
    handleSequence(message, message.video_note.file_id)
  
def handleStatic(message, file_id):
    if message.chat.type == 'private':
        bot.send_chat_action(message.chat.id, 'typing')
    response = download(file_id)
    if response.status_code == 200:
        nsfw = analyze(Image.open(BytesIO(response.content)))
        if message.chat.type == 'private':
            answerPrivate(message, nsfw)
        elif nsfw > NSFW_MAX:
            answerChat(message)

def handleSequence(message, file_id):
    if message.chat.type == 'private':
        bot.send_chat_action(message.chat.id, 'typing')
    response = download(file_id)
    if response.status_code == 200:
        max_nsfw = 0;
        container = av.open(BytesIO(response.content))
        video = next(s for s in container.streams) 
        total_frames = container.streams.video[0].frames
        for packet in container.demux(video):
            for frame in packet.decode():
                if frame.index % int(total_frames / SEQ_SCANS)  ==1:
                    nsfw = analyze(frame.to_image())
                    #print('Image analyzing. Frame: {0}, NSFW: {1}'.format(frame.index, nsfw))
                    if message.chat.type != 'private' and nsfw > NSFW_MAX:
                        answerChat(message)
                        return
                    elif nsfw > max_nsfw:
                        max_nsfw = nsfw
        if message.chat.type == 'private':
            answerPrivate(message, max_nsfw)

def download(file_id):
    file_info = bot.get_file(file_id)
    return requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(BOT_TOKEN, file_info.file_path))
   
def analyze(image):
    sfw, nsfw = classify(image)
    return nsfw

def answerPrivate(message, nsfw):
    bot.reply_to(message, "NSFW: {0}%".format(int(round(nsfw * 100)))) 

def answerChat(message):
    if bot.get_chat_member(message.chat.id, me.id).can_delete_messages:
        bot.delete_message(message.chat.id, message.id)
        bot.send_message(message.chat.id, '@{0} 👮'.format(message.from_user.username))

bot.infinity_polling()

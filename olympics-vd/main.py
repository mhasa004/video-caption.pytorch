import os
import json

def convert_time_str(tstr):
	tlist = list(map(float, tstr.split(':')))
	return tlist[0]*3600 + tlist[1]*60 + tlist[2]

if __name__ == '__main__':
	
	data_dir = '/home/ubuntu/data/olympics'

	# get the video list
	video_list = []
	with open(os.path.join(data_dir, 'video_list.txt')) as fid:
		for line in fid:
			if line[0] == '#':
				continue
			video_list.append(line.strip())

	
	# collect all the description and merge them
	all_caps = {}
	for video in video_list:
		script_path = os.path.join(data_dir, 'rawdata', 'Olympics_2018_DVS_damped_scripts', video+'.sbv')
		caps = []
		with open(script_path) as script_file:
			nextl = 1
			cap = []
			for line in script_file:
				if line.strip() == '':
					nextl = 1
					cap = []
				elif nextl == 1:
					cap += list(map(convert_time_str, line.split(',')))
					nextl = 2
				elif nextl == 2:
					cap += [line.strip()]
					caps.append(cap)
		
		merged_caps = [caps[0]]
		for cap in caps[1:]:
			if merged_caps[-1][1] >= cap[0]:
				merged_caps[-1][1] = cap[1]
				merged_caps[-1][2] += ' ' + cap[2]
			else:
				merged_caps.append(cap)

		all_caps[video] = merged_caps


	# filter out initial five minutes and adjust time

	for video in all_caps:
		caps = all_caps[video]
		new_caps = []
		for i, cap in enumerate(caps):
			if cap[1] <= 302:
				continue
			cap[0] -= 300
			cap[1] -= 300
			new_caps.append(cap)
		all_caps[video] = new_caps


	# generate ffmpeg commands for video segmentation
	fid = open(os.path.join(data_dir, 'cut_videos.sh'), 'w')
	video_dir = os.path.join(data_dir, 'rawdata', 'Olympics_2018_DVS')
	for video in all_caps:
		caps = all_caps[video]
		video_path = os.path.join(video_dir, video+'.mpg')
		for i, cap in enumerate(caps):
			cut_video_path = os.path.join(data_dir, 'cut-videos', '%s_%03d.mp4'%(video,i+1))
			fid.write('ffmpeg -i %s -ss %f -to %f -c copy %s -y\n'%(video_path, cap[0], cap[1], cut_video_path))
	fid.close()


	# generate caption file
	captions = {}
	for video in all_caps:
		caps = all_caps[video]
		for i, cap in enumerate(caps):
			cut_video_name = '%s_%03d'%(video,i+1)
			captions[cut_video_name] = {}
			captions[cut_video_name]['captions'] = [cap[2]]
			final_cap = cap[2].split()
			final_cap.insert(0, '<sos>')
			final_cap.append('<eos>')
			captions[cut_video_name]['final_captions'] = [final_cap]

	captions_path = os.path.join(data_dir, 'caption.json')
	with open(captions_path, 'w') as fid:
		json.dump(captions, fid)


	# generate video info
	vid = 0
	sen_id = 0
	video_info = {'videos':[], 'sentences':[]}
	video_dir = os.path.join(data_dir, 'rawdata', 'Olympics_2018_DVS')
	for video in all_caps:
		caps = all_caps[video]
		video_path = os.path.join(video_dir, video+'.mpg')
		for i, cap in enumerate(caps):
			cut_video_info = {}
			cut_video_info['category'] = 0
			cut_video_info['url'] = video_path
			cut_video_info['video_id'] = '%s_%03d'%(video,i+1)
			cut_video_info['start_time'] = cap[0]
			cut_video_info['end_time'] = cap[1]
			cut_video_info['split'] = 'train'
			cut_video_info['id'] = vid
			vid += 1
			video_info['videos'].append(cut_video_info)

			sen_info = {}
			sen_info['caption'] = cap[2]
			sen_info['video_id'] = '%s_%03d'%(video,i+1)
			sen_info['sen_id'] = sen_id
			sen_id += 1
			video_info['sentences'].append(sen_info)

	video_info_path = os.path.join(data_dir, 'video_info.json')
	with open(video_info_path, 'w') as fid:
		json.dump(video_info, fid)

		
				
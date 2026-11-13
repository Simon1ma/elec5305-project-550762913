function result = START_PROJECT(mode)
% Download/clone repository, set Current Folder here, run START_PROJECT.
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code','latency'));addpath(fullfile(root,'code','final'));addpath(fullfile(root,'code','scene'));
assert(~isempty(ver('signal')),'Signal Processing Toolbox is required.');
if nargin<1,mode='demo';end
switch lower(string(mode))
 case {"demo","enhancement"},result=run_public_demo(true);
 case {"check","test"},result=check_submission();
 case "personal"
  assert(isfile(fullfile(root,'data','local','scene_bridge','inputs','speech_04__container_press_04__snr0.mat')),'This mode needs the complete submission ZIP with private personal recordings.');
  [app,controls]=launch_final_demo('personal');result=struct('app',app,'controls',controls);
 case "personal_scene"
  assert(isfile(fullfile(root,'data','local','scene','development','development_manifest.json')),'This mode needs the complete submission ZIP with private personal recordings.');
  [app,controls]=launch_scene_demo('on','baseline');result=struct('app',app,'controls',controls);
 case "personal_check",result=check_personal_submission();
 case {"classification","advanced"}
  for item={'development','advanced'},folder=fullfile(root,'data','local','scene',item{1});if ~isfolder(folder),mkdir(folder);end,end
  copyfile(fullfile(root,'data','scene_models','scene_model.mat'),fullfile(root,'data','local','scene','development','scene_model.mat'));
  copyfile(fullfile(root,'data','scene_models','advanced_models.joblib'),fullfile(root,'data','local','scene','advanced','advanced_models.joblib'));
  d=load(fullfile(root,'data','demo_public','case.mat'));folder=fullfile(root,'data','local','public_demo');if ~isfolder(folder),mkdir(folder);end
  file=fullfile(folder,'public_clean.wav');audiowrite(file,d.clean,double(d.fs),'BitsPerSample',24);
  if string(mode)=="advanced"
   assert(~isempty(ver('audio')),'Advanced MFCC inference requires Audio Toolbox.');
   assert(isfile(fullfile(root,'data','local','scene','advanced','runtime.json')),'Install Python dependencies, then run python code/scene/configure_runtime.py.');
   result=classify_scene_advanced(file);
  else,result=classify_scene_file(file);end
  fprintf('Public speech example predicted as: %s\n',result.label);disp(result.features);
 otherwise,error('Use START_PROJECT, START_PROJECT(''check''), START_PROJECT(''classification'') or START_PROJECT(''advanced'').');
end
end

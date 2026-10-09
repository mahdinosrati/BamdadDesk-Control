'use strict';
const messages = {
  control:['CONTROL CENTER','مرکز مدیریت'],workspace:['YOUR ORGANIZATION. CONNECTED.','سازمان شما، متصل و یکپارچه'],
  welcome:['A clearer view of your workspace.','دیدی روشن‌تر به فضای کاری شما.'],intro:['Manage devices, access policies and client releases from one place.','دستگاه‌ها، سیاست‌های دسترسی و نسخه‌های برنامه را از یک جا مدیریت کنید.'],
  secure:['ADMINISTRATOR ACCESS','ورود مدیر سازمان'],signin:['Sign in','ورود'],signinHint:['Use your organization administrator account.','با حساب مدیریت سازمان خود وارد شوید.'],
  username:['Username','نام کاربری'],password:['Password','رمز عبور'],logout:['Sign out','خروج'],workspaceNav:['WORKSPACE','فضای کاری'],managed:['Managed access','دسترسی مدیریت‌شده'],
  sidebarHint:['Policies are confirmed by each device after they are applied.','اعمال سیاست‌ها توسط هر دستگاه تأیید می‌شود.'],footer:['Your workspace, within reach.','فضای کار شما، در دسترس شما.'],
  devices:['Devices','دستگاه‌ها'],policies:['Access policies','سیاست‌های دسترسی'],groups:['Groups','گروه‌ها'],enrollment:['Enroll devices','ثبت دستگاه'],releases:['Client releases','نسخه‌های کلاینت'],admins:['Administrators','مدیران'],audit:['Activity log','گزارش فعالیت'],
  overview:['Workspace overview','نمای کلی سازمان'],devicesHint:['A live view of your managed devices and policy status.','وضعیت دستگاه‌های مدیریت‌شده و نتیجهٔ اعمال سیاست‌ها.'],
  total:['Total devices','تمام دستگاه‌ها'],online:['Online','آنلاین'],pending:['Pending policy','در انتظار سیاست'],updated:['Policy applied','سیاست اعمال شده'],
  search:['Search devices…','جست‌وجوی دستگاه…'],refresh:['Refresh','تازه‌سازی'],name:['Name','نام'],group:['Group','گروه'],version:['Version','نسخه'],status:['Status','وضعیت'],policy:['Policy','سیاست'],lastSeen:['Last seen','آخرین حضور'],
  offline:['Offline','آفلاین'],disabled:['Disabled','غیرفعال'],applied:['Applied','اعمال شده'],waiting:['Waiting','در انتظار'],error:['Error','خطا'],none:['None','بدون گروه'],never:['Never','هنوز متصل نشده'],
  emptyDevices:['No devices enrolled yet','هنوز دستگاهی ثبت نشده'],emptyDevicesHint:['Create an enrollment token to connect your first managed client.','برای اتصال اولین کلاینت مدیریتی، توکن ثبت دستگاه بسازید.'],
  save:['Save changes','ذخیره تغییرات'],saved:['Changes saved','تغییرات ذخیره شد'],active:['Active','فعال'],cancel:['Cancel','انصراف'],edit:['Edit','ویرایش'],
  policiesHint:['Define organization defaults, then override by group or device.','پیش‌فرض سازمان را تعیین کنید و برای گروه یا دستگاه تغییر دهید.'],scope:['Policy scope','محدوده سیاست'],global:['Entire organization','کل سازمان'],
  inherit:['Inherit / unmanaged','ارث‌بری / مدیریت‌نشده'],allow:['Enabled','فعال'],deny:['Disabled','غیرفعال'],policyNote:['Changes apply when devices next check in. Active remote sessions may retain their current permissions.','تغییرات در ارتباط بعدی دستگاه اعمال می‌شوند. نشست‌های ریموت فعال ممکن است دسترسی‌های فعلی خود را حفظ کنند.'],
  access:['Access permissions','مجوزهای دسترسی'],connection:['Connection settings','تنظیمات اتصال'],newPassword:['New permanent remote password','رمز ثابت جدید اتصال ریموت'],passwordHint:['Leave blank to keep the current policy password. One-time passwords remain available when both methods are enabled.','برای حفظ رمز فعلی سیاست، خالی بگذارید. با فعال بودن هر دو روش، رمز یک‌بارمصرف نیز قابل استفاده است.'],
  passwordSet:['A password override is set for this scope.','برای این محدوده رمز اختصاصی تعیین شده است.'],passwordInherited:['No password override at this scope.','برای این محدوده رمز اختصاصی تعیین نشده است.'],clearPassword:['Remove this scope’s password override','حذف رمز اختصاصی این محدوده'],
  groupsHint:['Organize devices into teams, locations or departments.','دستگاه‌ها را بر اساس تیم، محل یا واحد سازمانی گروه‌بندی کنید.'],addGroup:['Create group','ساخت گروه'],groupName:['Group name','نام گروه'],
  enrollHint:['Create a temporary token for authorized organization devices.','برای دستگاه‌های مجاز سازمان توکن موقت ایجاد کنید.'],label:['Token label','عنوان توکن'],hours:['Valid for (hours)','اعتبار (ساعت)'],uses:['Maximum devices','حداکثر دستگاه'],createToken:['Create enrollment token','ساخت توکن ثبت'],
  tokenNotice:['Copy this token now. It is shown only once. Transfer it to devices through your authorized deployment process.','توکن را اکنون کپی کنید؛ فقط همین بار نمایش داده می‌شود. آن را از مسیر استقرار مجاز به دستگاه‌ها منتقل کنید.'],publicKey:['Pinned policy public key','کلید عمومی مورد اعتماد سیاست'],panelUrl:['Panel URL','آدرس پنل'],expires:['Expires','انقضا'],
  releaseHint:['Upload Windows x64 builds and publish a verified update for your users.','ساخت‌های ویندوز x64 را بارگذاری و برای کاربران منتشر کنید.'],upload:['Upload release','بارگذاری نسخه'],file:['Windows executable (.exe)','فایل اجرایی ویندوز (.exe)'],publish:['Publish update','انتشار به‌روزرسانی'],published:['Published','منتشر شده'],draft:['Draft','پیش‌نویس'],size:['Size','حجم'],
  releaseNote:['Uploading creates a draft. Publishing offers the update to managed clients; installation requires the user’s action.','بارگذاری، پیش‌نویس می‌سازد. انتشار، به‌روزرسانی را به کلاینت‌های مدیریتی پیشنهاد می‌دهد؛ نصب با اقدام کاربر انجام می‌شود.'],confirmPublish:['Publish this version for all managed devices?','این نسخه برای تمام دستگاه‌های مدیریتی منتشر شود؟'],
  adminHint:['Give each administrator only the capabilities they need.','برای هر مدیر دسترسی‌های مورد نیازش را تعیین کنید.'],addAdmin:['Add administrator','افزودن مدیر'],permissions:['Permissions','دسترسی‌ها'],adminPassword:['Administrator password (12+ characters)','رمز مدیر (حداقل ۱۲ کاراکتر)'],
  auditHint:['Changes and sign-ins, recorded without passwords or tokens.','تغییرات و ورودها، بدون ثبت رمز یا توکن.'],time:['Time','زمان'],actor:['Administrator / device','مدیر / دستگاه'],action:['Action','عملیات'],target:['Target','مقصد'],empty:['Nothing here yet','هنوز موردی وجود ندارد'],loading:['Loading…','در حال دریافت…'],
  'devices.read':['View devices','مشاهده دستگاه‌ها'],'devices.write':['Manage devices and groups','مدیریت دستگاه‌ها و گروه‌ها'],'policies.write':['Edit policies and remote passwords','تغییر سیاست‌ها و رمز ریموت'],'enrollment.write':['Create enrollment tokens','ساخت توکن ثبت دستگاه'],'releases.read':['View releases','مشاهده نسخه‌ها'],'releases.write':['Upload and publish updates','بارگذاری و انتشار نسخه‌ها'],'admins.write':['Manage administrators and their permissions','مدیریت مدیران و دسترسی آنان'],'audit.read':['View activity log','مشاهده گزارش فعالیت'],
  'verification-method':['Password methods','روش‌های رمز عبور'],'approve-mode':['Connection approval','تأیید اتصال'],'access-mode':['Permission mode','حالت دسترسی'],'temporary-password-length':['One-time password length','طول رمز یک‌بارمصرف'],
  'use-both-passwords':['Permanent + one-time','ثابت + یک‌بارمصرف'],'use-permanent-password':['Permanent only','فقط ثابت'],'use-temporary-password':['One-time only','فقط یک‌بارمصرف'],
  click:['Manual acceptance','پذیرش دستی'],'password-click':['Password + manual acceptance','رمز + پذیرش دستی'],custom:['Custom permissions','دسترسی سفارشی']
};
let language = localStorage.getItem('bamdad-language') === 'fa' ? 'fa' : 'en';
let user = null, csrf = '', view = 'dashboard', catalog = [], allPermissions = [], groups = [], devices = [], revision = 1;
const $ = s => document.querySelector(s);
const t = key => messages[key]?.[language === 'fa' ? 1 : 0] || key;
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key,value] of Object.entries(attrs)) {
    if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'checked' || key === 'disabled' || key === 'hidden') node[key] = Boolean(value);
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) if (child !== null && child !== undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return node;
}
function button(text, action, quiet = false) {return el('button', {type:'button', class:quiet?'quiet':'', onclick:action}, t(text));}
function notice(message, error = false) {const n=$('#notice'); n.textContent=message;n.className=error?'error':'';n.hidden=false;clearTimeout(notice.timer);notice.timer=setTimeout(()=>n.hidden=true,7000);}
async function api(path, options = {}) {
  const response = await fetch('/api'+path,{...options,headers:{...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),'X-CSRF-Token':csrf,...options.headers}});
  if (!response.ok) {
    const value = await response.json().catch(()=>({detail:response.statusText}));
    if (response.status===401 && path!=='/login') showLogin();
    throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail));
  }
  return response.json();
}
const send = (path, body, method='POST') => api(path,{method,body:JSON.stringify(body)});
const can = p => user?.permissions.includes(p);
function date(value) {return value ? new Date(value*1000).toLocaleString(language==='fa'?'fa-IR':'en-GB') : t('never');}
function badge(text, kind='') {return el('span',{class:'badge '+kind},t(text));}
function field(label, input) {return el('label',{},el('span',{},t(label)),input);}
function input(name,type='text',value='') {return el('input',{name,type,value});}
function select(options, value='') {const node=el('select');for(const [v,label] of options) node.append(el('option',{value:v},label));node.value=options.some(([v])=>v===value)?value:(options[0]?.[0]||'');return node;}
function heading(title, hint, action) {return el('div',{class:'page-heading'},el('div',{},el('span',{class:'eyebrow'},'BAMDADDESK / CONTROL'),el('h1',{},t(title)),el('p',{},t(hint))),action);}
function empty(title='empty',hint) {return el('div',{class:'empty'},el('strong',{},t(title)),hint?t(hint):'');}
function table(headings, rows) {return el('div',{class:'table-wrap'},el('table',{},el('thead',{},el('tr',{},headings.map(h=>el('th',{},t(h))))),el('tbody',{},rows)));}
function modal(...children) {$('#dialog-body').replaceChildren(...children);$('#dialog').showModal();}
function applyLanguage() {
  document.documentElement.lang=language;document.documentElement.dir=language==='fa'?'rtl':'ltr';
  document.querySelectorAll('[data-i18n]').forEach(n=>n.textContent=t(n.dataset.i18n));
  $('#language').textContent=language==='en'?'فارسی':'English';$('#language').lang=language==='en'?'fa':'en';
}
$('#language').addEventListener('click',()=>{language=language==='en'?'fa':'en';localStorage.setItem('bamdad-language',language);applyLanguage();if(user){navigation();loadView();}});
function showLogin() {user=null;csrf='';$('#workspace').hidden=true;$('#login-screen').hidden=false;$('#logout').hidden=true;$('#identity').textContent='';}
async function start() {
  user=await api('/me');csrf=user.csrf;const data=await api('/catalog');catalog=data.options;allPermissions=data.permissions;
  $('#login-screen').hidden=true;$('#workspace').hidden=false;$('#logout').hidden=false;$('#identity').textContent=user.username;
  navigation();await loadView();
}
$('#login-form').addEventListener('submit',async event=>{event.preventDefault();const form=event.currentTarget;const submit=form.querySelector('button[type=submit]');submit.disabled=true;try{await send('/login',{username:form.username.value,password:form.password.value});form.password.value='';await start();}catch(e){notice(e.message,true);}finally{submit.disabled=false;}});
$('#logout').addEventListener('click',async()=>{try{await send('/logout',{});showLogin();}catch(e){notice(e.message,true);}});
function navigation() {
  const items=[['dashboard','devices.read'],['devices','devices.read'],['connections','audit.read'],['policies','policies.write'],['groups','devices.read'],['enrollment','enrollment.write'],['releases','releases.read'],['admins','admins.write'],['audit','audit.read']].filter(([,p])=>can(p));
  if (!items.some(([key])=>key===view)) view=items[0]?.[0]||'';
  $('#navigation').replaceChildren(...items.map(([key])=>el('button',{class:view===key?'active':'',onclick:()=>{view=key;navigation();loadView();}},t(key))));
}
async function loadView() {
  $('#content').replaceChildren(el('p',{class:'muted'},t('loading')));
  try {await ({dashboard:renderDashboard,connections:renderConnections,devices:renderDevices,policies:renderPolicies,groups:renderGroups,enrollment:renderEnrollment,releases:renderReleases,admins:renderAdmins,audit:renderAudit}[view]||(()=>$('#content').replaceChildren(empty())))();}
  catch(e){$('#content').replaceChildren(el('div',{class:'notice-inline'},e.message));notice(e.message,true);}
}
async function fetchGroups(){groups=can('devices.read')?await api('/groups'):[];}
const groupOptions=()=>[...(user.groups===null?[['',t('none')]]:[]),...groups.map(g=>[g.id,g.name])];
async function renderDevices() {
  const result=await api('/devices');devices=result.devices;revision=result.revision;await fetchGroups();
  const now=Date.now()/1000, online=devices.filter(d=>d.active&&now-d.last_seen<150).length;
  const stats=el('div',{class:'stats'},[['total',devices.length],['online',online],['pending',devices.filter(d=>d.active&&d.applied<revision).length],['updated',devices.filter(d=>d.applied===revision).length]].map(([key,value])=>el('div',{class:'glass stat'},el('span',{class:'label'},t(key)),el('span',{class:'value'},value))));
  const results=el('div');const search=input('search');search.placeholder=t('search');
  const draw=()=>{
    const filtered=devices.filter(d=>(d.name+' '+d.rustdesk_id+' '+d.version).toLowerCase().includes(search.value.toLowerCase()));
    results.replaceChildren(devices.length?table(['name','group','version','status','policy','lastSeen',''],filtered.map(d=>el('tr',{},
      el('td',{},el('span',{class:'device-name'},d.name),el('span',{class:'device-id'},d.rustdesk_id||d.id)),
      el('td',{},groups.find(g=>g.id===d.group_id)?.name||t('none')),el('td',{class:'ltr'},d.version),
      el('td',{},badge(!d.active?'disabled':now-d.last_seen<150?'online':'offline',d.active&&now-d.last_seen<150?'':'offline')),
      el('td',{},badge(d.error?'error':d.applied===revision?'applied':'waiting',d.error?'error':d.applied===revision?'':'pending')),
      el('td',{},date(d.last_seen)),el('td',{},button('details',()=>renderDeviceDetails(d.id),true),can('devices.write')?button('edit',()=>deviceDialog(d),true):'')))):empty('emptyDevices','emptyDevicesHint'));
  };search.addEventListener('input',draw);draw();
  $('#content').replaceChildren(heading('overview','devicesHint',button('refresh',loadView,true)),stats,el('section',{class:'card'},el('div',{class:'toolbar'},search,el('span',{class:'spacer'}),el('span',{class:'muted small'},t('policy')+' #'+revision)),results));
}
function deviceDialog(device){
  const group=select(groupOptions(),device.group_id),active=input('active','checkbox');active.checked=Boolean(device.active);
  modal(el('h2',{},device.name),el('p',{class:'ltr muted'},device.id),field('group',group),el('label',{class:'check'},active,t('managementState')),el('p',{class:'muted small'},t('managementHint')),device.error?el('p',{class:'notice-inline'},device.error):el('span'),el('div',{class:'actions'},button('save',async()=>{try{await send('/devices/'+device.id,{group_id:group.value,active:active.checked},'PUT');$('#dialog').close();await renderDevices();notice(t('saved'));}catch(e){notice(e.message,true);}})));
}
async function renderGroups(){
  await fetchGroups();const name=input('name');name.required=true;name.maxLength=100;
  const form=el('form',{class:'toolbar',onsubmit:async e=>{e.preventDefault();try{await send('/groups',{name:name.value.trim()});await renderGroups();notice(t('saved'));}catch(e){notice(e.message,true);}}},name,el('button',{type:'submit'},t('addGroup')));name.placeholder=t('groupName');
  $('#content').replaceChildren(heading('groups','groupsHint'),el('section',{class:'card'},can('devices.write')&&user.groups===null?form:null,groups.length?table(['name',''],groups.map(g=>el('tr',{},el('td',{},g.name),el('td',{class:'ltr muted'},g.id)))):empty()));
}
async function renderPolicies(){
  await fetchGroups();if(can('devices.read')) devices=(await api('/devices')).devices;
  const scope=select([...(user.groups===null?[['global',t('global')]]:[]),...groups.map(g=>['group:'+g.id,t('group')+': '+g.name]),...devices.map(d=>['device:'+d.id,t('devices')+': '+d.name])]);
  if(!scope.options.length){$('#content').replaceChildren(heading('policies','policiesHint'),empty('noScope'));return;}
  const editor=el('div');
  const load=async()=>{try{
    const policy=await api('/policies/'+encodeURIComponent(scope.value));const values=new Map();
    const rows=catalog.map(option=>{
      const title=messages[option.key]?t(option.key):option[language];
      const control=option.values?select([['',t('inherit')],...option.values.map(v=>[v,v==='Y'?t('allow'):v==='N'?t('deny'):t(v)])],policy.options[option.key]||''):input(option.key,'text',policy.options[option.key]||'');
      if(!option.values) control.classList.add('ltr');values.set(option.key,control);control.id='policy-'+option.key;
      return el('div',{class:'policy-row'+(!option.values?' text-option':'')},el('label',{for:control.id},title),control);
    });
    const password=input('new-password','password');password.autocomplete='new-password';password.maxLength=128;
    const clear=input('clear','checkbox');
    const save=button('save',async()=>{save.disabled=true;try{const options={};for(const [key,control] of values)if(control.value)options[key]=control.value;
      await send('/policies/'+encodeURIComponent(scope.value),{options,password:password.value||null,clear_password_override:clear.checked,expected_revision:policy.revision},'PUT');password.value='';await load();notice(t('saved'));
    }catch(e){notice(e.message,true);}finally{save.disabled=false;}});
    editor.replaceChildren(el('section',{class:'card'},el('h2',{},t('access')),el('div',{class:'policy-grid'},rows)),el('section',{class:'card'},el('h2',{},t('newPassword')),el('p',{class:'muted'},t('passwordHint')),el('p',{class:'small cyan'},t(policy.has_password?'passwordSet':'passwordInherited')),password,el('label',{class:'check'},clear,t('clearPassword')),el('div',{class:'actions'},save)));
  }catch(e){notice(e.message,true);}};
  scope.addEventListener('change',load);
  $('#content').replaceChildren(heading('policies','policiesHint'),el('div',{class:'notice-inline'},t('policyNote')),el('div',{class:'card'},field('scope',scope)),editor);await load();
}
async function renderEnrollment(){
  await fetchGroups();const label=input('label');label.required=true;label.maxLength=100;const group=select(groupOptions());
  const hours=input('hours','number','24');hours.min='1';hours.max='168';const uses=input('uses','number','1');uses.min='1';uses.max='1000';
  const form=el('form',{class:'card form-grid',onsubmit:async e=>{e.preventDefault();try{const result=await send('/enrollments',{label:label.value,group_id:group.value,hours:Number(hours.value),uses:Number(uses.value)});
    modal(el('h2',{},t('enrollment')),el('p',{class:'notice-inline'},t('tokenNotice')),el('h3',{},t('panelUrl')),el('code',{class:'secret ltr'},location.origin),el('h3',{},t('publicKey')),el('code',{class:'secret ltr'},result.public_key),el('h3',{},t('createToken')),el('code',{class:'secret ltr'},result.token),el('p',{class:'muted'},t('expires')+': '+date(result.expires)));
  }catch(e){notice(e.message,true);}}},field('label',label),field('group',group),el('div',{class:'grid'},field('hours',hours),field('uses',uses)),el('button',{type:'submit'},t('createToken')));
  $('#content').replaceChildren(heading('enrollment','enrollHint'),form);
}
async function renderReleases(){
  const releases=await api('/releases');const version=input('version','text');version.placeholder='1.5.1';version.required=true;version.pattern='[0-9]+\\.[0-9]+\\.[0-9]+';
  const file=input('file','file');file.accept='.exe';file.required=true;
  const submit=el('button',{type:'submit'},t('upload'));
  const form=el('form',{class:'card form-grid',onsubmit:async e=>{e.preventDefault();submit.disabled=true;try{const data=new FormData();data.append('file',file.files[0]);await api('/releases?version='+encodeURIComponent(version.value),{method:'POST',body:data});await renderReleases();notice(t('saved'));}catch(e){notice(e.message,true);}finally{submit.disabled=false;}}},el('h2',{},t('upload')),el('div',{class:'grid'},field('version',version),field('file',file)),submit);
  const rows=releases.map(r=>el('tr',{},el('td',{class:'ltr'},r.version),el('td',{},(r.size/1048576).toFixed(1)+' MB'),el('td',{},badge(r.published?'published':'draft',r.published?'':'offline')),el('td',{class:'ltr small',title:r.sha256},r.sha256.slice(0,16)+'…'),el('td',{},!r.published&&can('releases.write')?button('publish',()=>{modal(el('h2',{},t('confirmPublish')),el('p',{class:'ltr'},r.version),el('div',{class:'actions'},button('publish',async()=>{try{await send('/releases/'+r.id+'/publish',{});$('#dialog').close();await renderReleases();notice(t('saved'));}catch(e){notice(e.message,true);}}),button('cancel',()=>$('#dialog').close(),true)));},true):'')));
  $('#content').replaceChildren(heading('releases','releaseHint'),el('div',{class:'notice-inline'},t('releaseNote')),can('releases.write')?form:el('span'),el('section',{class:'card'},rows.length?table(['version','size','status','SHA256',''],rows):empty()));
}
async function renderAdmins(){
  await fetchGroups();
  const admins=await api('/admins');$('#content').replaceChildren(heading('admins','adminHint',button('addAdmin',()=>adminDialog())),el('section',{class:'card'},table(['username','permissions','status',''],admins.map(a=>el('tr',{},el('td',{},a.username),el('td',{},a.permissions.length+' / '+allPermissions.length),el('td',{},badge(a.active?'active':'disabled',a.active?'':'offline')),el('td',{},button('edit',()=>adminDialog(a),true)))))));
}
function adminDialog(admin){
  const globalScope=input('global-scope','checkbox');globalScope.checked=admin?admin.groups===null:true;
  const groupChecks=groups.map(g=>{const box=input('group-'+g.id,'checkbox');box.checked=Boolean(admin?.groups?.includes(g.id));return [g,box];});
  const username=input('username','text',admin?.username||'');username.required=true;username.maxLength=80;username.disabled=Boolean(admin);
  const password=input('password','password');password.required=!admin;password.minLength=12;password.maxLength=256;password.autocomplete='new-password';
  const checks=allPermissions.map(p=>{const box=input(p,'checkbox');box.checked=Boolean(admin?.permissions.includes(p));return [p,box];});
  const active=input('active','checkbox');active.checked=admin?Boolean(admin.active):true;
  modal(el('h2',{},t(admin?'edit':'addAdmin')),el('form',{class:'form-grid',onsubmit:async e=>{e.preventDefault();try{const permissions=checks.filter(([,box])=>box.checked).map(([p])=>p);
    const scopeGroups=globalScope.checked?null:groupChecks.filter(([,box])=>box.checked).map(([g])=>g.id);
    if(admin)await send('/admins/'+admin.id,{permissions,groups:scopeGroups,active:active.checked,password:password.value||null},'PUT');else await send('/admins',{username:username.value,password:password.value,permissions,groups:scopeGroups});
    $('#dialog').close();if(admin?.id===user.id){showLogin();}else await renderAdmins();notice(t('saved'));
  }catch(e){notice(e.message,true);}}},field('username',username),field('adminPassword',password),el('h3',{},t('scope')),el('label',{class:'check'},globalScope,t('organizationScope')),el('p',{class:'muted small'},t('scopeHint')),groupChecks.map(([g,box])=>el('label',{class:'check'},box,g.name)),el('div',{},el('h3',{},t('permissions')),checks.map(([p,box])=>el('label',{class:'check'},box,t(p)))),admin?el('label',{class:'check'},active,t('active')):null,el('button',{type:'submit'},t('save'))));
}
async function renderAudit(){const rows=await api('/audit');$('#content').replaceChildren(heading('audit','auditHint',button('refresh',loadView,true)),el('section',{class:'card'},rows.length?table(['time','actor','action','target'],rows.map(r=>el('tr',{},el('td',{},date(r.created)),el('td',{},r.actor),el('td',{class:'ltr'},r.action),el('td',{class:'ltr'},r.target)))):empty()));}
Object.assign(messages,{
  dashboard:['Overview','داشبورد'],connections:['Connection history','گزارش اتصال‌ها'],details:['Details','جزئیات'],
  analyticsHint:['Device health and reported connection activity in your permitted groups.','وضعیت دستگاه‌ها و اتصال‌های گزارش‌شده در گروه‌های مجاز شما.'],
  daily:['Authorized connections · last 14 days · UTC','اتصال‌های تأییدشده در ۱۴ روز اخیر به وقت UTC'],versions:['Client versions','نسخه‌های کلاینت'],groupDistribution:['Devices by group','دستگاه‌ها به تفکیک گروه'],errors:['Devices reporting an error','دستگاه‌های دارای خطا'],
  noData:['No recorded activity in this period','در این بازه فعالیتی ثبت نشده است'],noScope:['No groups assigned to this administrator','گروهی به این مدیر اختصاص داده نشده است'],
  organizationScope:['Entire organization','تمام سازمان'],scopeHint:['Uncheck to limit access to selected groups. Scoped admins cannot manage administrators or publish organization-wide releases.','برای محدودکردن دسترسی، تیک تمام سازمان را بردارید و گروه‌ها را انتخاب کنید. مدیر محدود به گروه نمی‌تواند مدیران را تغییر دهد یا نسخهٔ سراسری منتشر کند.'],
  alias:['Display name','نام نمایشی'],note:['IT notes','یادداشت پشتیبانی'],platform:['Operating system / architecture','سیستم‌عامل و معماری'],reportedUser:['Reported Windows user','کاربر گزارش‌شدهٔ ویندوز'],effective:['Effective policy','سیاست مؤثر'],
  connect:['Open BamdadDesk','بازکردن BamdadDesk'],connectHint:['Opens the installed desktop client. Remote authentication is still required. This does not start a browser session.','برنامهٔ نصب‌شده را باز می‌کند و احراز هویت ریموت همچنان لازم است. اتصال داخل مرورگر نیست.'],
  value:['Value','مقدار'],managementState:['Management enrollment enabled','ارتباط مدیریتی دستگاه فعال باشد'],managementHint:['Disabling management stops panel communication; it does not block remote desktop access.','غیرفعال‌کردن مدیریت، ارتباط با پنل را قطع می‌کند؛ دسترسی ریموت دستگاه مسدود نمی‌شود.'],
  connectionHint:['Events reported by managed Windows services. Missing close events do not prove a session is still active.','رویدادهای گزارش‌شده توسط سرویس‌های مدیریتی ویندوز. نبود رویداد پایان به معنی فعال‌بودن نشست نیست.'],
  duration:['Observed duration (s)','مدت ثبت‌شده (ثانیه)'],peer:['Reported peer','طرف مقابل گزارش‌شده'],session:['Session','نشست'],opened:['Opened','شروع ارتباط'],authorized:['Authorized','احراز هویت موفق'],closed:['Closed','پایان ارتباط'],
  identityHint:['Peer names and IDs are client-reported and are not verified panel administrator identities. Events queued in memory can be lost on service restart or extended outage.','نام و شناسهٔ طرف مقابل توسط کلاینت اعلام می‌شوند و هویت تأییدشدهٔ ادمین پنل نیستند. رویدادهای حافظه ممکن است هنگام راه‌اندازی مجدد سرویس یا قطعی طولانی از دست بروند.'],
  older:['Older events','رویدادهای قدیمی‌تر'],back:['Back to devices','بازگشت به دستگاه‌ها'],'devices.connect':['Launch desktop connections','بازکردن اتصال در برنامه'],
});

function bars(title, entries){
  const maximum=Math.max(1,...entries.map(([,count])=>count));
  return el('section',{class:'card chart-card'},el('h2',{},t(title)),entries.length?el('div',{class:'chart-bars'},entries.map(([label,count])=>el('div',{class:'chart-row'},el('span',{class:'chart-label',title:label},label),el('progress',{max:maximum,value:count,'aria-label':label+': '+count}),el('strong',{},count)))):empty('noData'));
}
async function renderDashboard(){
  const data=await api('/dashboard');
  const stats=el('div',{class:'stats'},[['total',data.total],['online',data.online],['pending',data.pending],['errors',data.errors]].map(([label,count])=>el('div',{class:'glass stat'},el('span',{class:'label'},t(label)),el('span',{class:'value'},count))));
  const days=Array.from({length:14},(_,i)=>{const day=new Date(Date.now()-(13-i)*86400000).toISOString().slice(0,10);return [day,data.daily.find(d=>d.day===day)?.count||0];});
  $('#content').replaceChildren(heading('dashboard','analyticsHint',button('refresh',loadView,true)),stats,el('div',{class:'charts-grid'},data.can_read_connections?bars('daily',days):null,bars('versions',Object.entries(data.versions)),bars('groupDistribution',data.groups.map(g=>[g.name,g.count]))));
}
function eventTable(events){return table(['time','devices','action','peer','session','duration'],events.map(e=>el('tr',{},el('td',{},date(e.occurred)),el('td',{},e.device_name||e.device),el('td',{},badge(e.kind,e.kind==='authorized'?'':'offline')),el('td',{},el('strong',{},e.peer_name||'—'),el('div',{class:'ltr small muted'},e.peer_id+' '+e.peer_ip)),el('td',{class:'ltr small',title:e.session_id},e.session_id.slice(-12)),el('td',{class:'ltr'},e.duration_seconds??'—'))));}
async function renderConnections(before){
  const data=await api('/connections'+(before?'?before='+before:''));
  $('#content').replaceChildren(heading('connections','connectionHint',button('refresh',()=>renderConnections(),true)),el('p',{class:'notice-inline'},t('identityHint')),el('section',{class:'card'},data.events.length?eventTable(data.events):empty('noData')),data.next_before?button('older',()=>renderConnections(data.next_before),true):document.createDocumentFragment());
}
async function renderDeviceDetails(identifier){
  try{
    const data=await api('/devices/'+identifier),d=data.device,m=data.details;await fetchGroups();
    const info=el('dl',{class:'device-facts'});
    for(const [label,value] of [['name',d.name],['group',groups.find(g=>g.id===d.group_id)?.name||t('none')],['version',d.version],['platform',m.platform],['reportedUser',m.username],['lastSeen',date(d.last_seen)],['policy',d.applied+' / '+data.policy.revision]]) info.append(el('dt',{},t(label)),el('dd',{},value||'—'));
    const alias=input('alias','text',m.alias||''),note=el('textarea',{rows:4,maxlength:2000});alias.maxLength=100;note.value=m.note||'';
    const group=select(groupOptions(),d.group_id),active=input('active','checkbox');active.checked=Boolean(d.active);
    const save=button('save',async()=>{try{await send('/devices/'+identifier,{group_id:group.value,active:active.checked,alias:alias.value,note:note.value},'PUT');notice(t('saved'));await renderDeviceDetails(identifier);}catch(e){notice(e.message,true);}});
    const launcher=can('devices.connect')?button('connect',async()=>{try{const result=await send('/devices/'+identifier+'/connect',{});modal(el('h2',{},t('connect')),el('p',{},t('connectHint')),el('a',{href:result.url,class:'launch-link'},t('connect')));}catch(e){notice(e.message,true);}}):null;
    const options=Object.entries(data.policy.options).map(([key,value])=>el('tr',{},el('td',{},catalog.find(o=>o.key===key)?.[language]||t(key)),el('td',{class:'ltr'},t(value))));
    $('#content').replaceChildren(heading(m.alias||d.name,'connectHint',button('back',renderDevices,true)),el('div',{class:'device-title'},badge(data.online?'online':'offline',data.online?'':'offline'),el('code',{class:'ltr'},d.rustdesk_id||d.id),launcher),el('div',{class:'details-grid'},el('section',{class:'card'},info,d.error?el('p',{class:'notice-inline'},d.error):null),el('section',{class:'card'},can('devices.write')?el('div',{class:'form-grid'},field('alias',alias),field('note',note),field('group',group),el('label',{class:'check'},active,t('managementState')),el('p',{class:'muted small'},t('managementHint')),save):el('p',{},m.note||'—'))),el('section',{class:'card'},el('h2',{},t('effective')),table(['name','value'],options)),can('audit.read')?el('section',{class:'card'},el('h2',{},t('connections')),data.events.length?eventTable(data.events):empty('noData')):document.createDocumentFragment());
  }catch(e){notice(e.message,true);}
}
applyLanguage();start().catch(()=>showLogin());

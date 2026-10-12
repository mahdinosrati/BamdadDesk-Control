'use strict';
Object.assign(messages, {
  about:['About','دربارهٔ ما'],showPassword:['Show password','نمایش رمز'],hidePassword:['Hide password','مخفی‌کردن رمز'],
  revoked:['Revoked','لغوشده'],expired:['Expired','منقضی'],exhausted:['Exhausted','تمام‌شده'],revoke:['Revoke token','لغو توکن'],
  remaining:['Remaining registrations','ثبت باقی‌مانده'],used:['Used registrations','تعداد استفاده'],unknown:['Unknown (legacy token)','نامشخص (توکن قدیمی)'],
  renewHours:['Renew from now (hours; blank keeps expiry)','تمدید از اکنون (ساعت؛ خالی = حفظ انقضا)'],
  removeGroup:['Delete group','حذف گروه'],destination:['Move existing devices to','انتقال دستگاه‌های موجود به'],
  removalHint:['Group policy will be removed, its tokens revoked and its administrator scopes removed. Devices inherit destination policies.','سیاست گروه حذف، توکن‌هایش لغو و دسترسی مدیران به این گروه برداشته می‌شود. دستگاه‌ها سیاست مقصد را می‌گیرند.'],
  members:['Members','اعضا'],passwordSource:['Current password source','منبع رمز فعلی'],
  'client-default':['Client preset (not readable by the panel)','پیش‌فرض کلاینت (در پنل قابل خواندن نیست)'],
  passwordIrrecoverable:['Stored password hashes cannot be displayed. Enter a new password to replace it.','متن رمز از هش ذخیره‌شده قابل نمایش نیست؛ برای تغییر، رمز جدید وارد کنید.'],
  requiredHint:['Complete required fields; administrator passwords need at least 12 characters.','فیلدهای الزامی را کامل کنید؛ رمز مدیر باید حداقل ۱۲ کاراکتر باشد.']
});

function enhancePasswords(root=document){
  root.querySelectorAll('input[type=password]').forEach(node=>{
    if(node.dataset.revealReady)return;
    node.dataset.revealReady='1';
    const wrap=el('span',{class:'password-control'}), toggle=button('showPassword',()=>{
      node.type=node.type==='password'?'text':'password';
      toggle.textContent=t(node.type==='password'?'showPassword':'hidePassword');
      toggle.setAttribute('aria-pressed',String(node.type==='text'));
    },true);
    toggle.setAttribute('aria-pressed','false');
    node.replaceWith(wrap);wrap.append(node,toggle);
  });
}
document.addEventListener('invalid',()=>notice(t('requiredHint'),true),true);
enhancePasswords();

function renderAbout(){
  $('#content').replaceChildren(heading('about',''),el('section',{class:'card'},
    el('h2',{},language==='fa'?'طراحی و توسعه: مهدی نصرتی':'Created by Mahdi Nosrati — مهدی نصرتی'),
    el('p',{},el('a',{href:'mailto:mahdinosrati06@gmail.com'},'mahdinosrati06@gmail.com')),
    el('p',{},el('a',{href:'https://t.me/MiNosrati',target:'_blank',rel:'noopener noreferrer'},'Telegram: @MiNosrati')),
    el('p',{},'BamdadDesk Control · AGPL-3.0'),
    el('p',{class:'muted'},language==='fa'?'کلاینت BamdadDesk بر پایهٔ RustDesk است؛ حقوق و مجوزهای پروژه‌های بالادستی محفوظ است.':'The BamdadDesk client is based on RustDesk. Upstream attribution and licenses are retained.')));
}

const originalGroups=renderGroups;
renderGroups=async function(){
  await originalGroups();
  const list=el('section',{class:'card'});
  for(const group of groups){
    const actions=el('div',{class:'toolbar'},el('strong',{},group.name),button('members',async()=>{
      try{const result=await api('/devices');devices=result.devices;
        modal(el('h2',{},group.name),...devices.filter(d=>d.group_id===group.id).map(d=>el('div',{class:'toolbar'},d.name,can('devices.write')?button('edit',()=>deviceDialog(d),true):null)));
      }catch(e){notice(e.message,true);}
    },true));
    if(can('policies.write'))actions.append(button('policies',async()=>{view='policies';navigation();await renderPolicies();const scope=$('#content select');scope.value='group:'+group.id;scope.dispatchEvent(new Event('change'));},true));
    if(can('devices.write'))actions.append(button('edit',()=>{
      const name=input('group-name','text',group.name);name.required=true;name.maxLength=100;
      modal(el('h2',{},t('edit')),el('form',{onsubmit:async e=>{e.preventDefault();try{await send('/groups/'+group.id,{name:name.value.trim()},'PUT');$('#dialog').close();await renderGroups();notice(t('saved'));}catch(err){notice(err.message,true);}}},field('groupName',name),el('button',{type:'submit'},t('save'))));
    },true));
    if(can('devices.write')&&user.groups===null)actions.append(button('removeGroup',()=>{
      const dest=select(groupOptions().filter(([id])=>id!==group.id));
      modal(el('h2',{},t('removeGroup')+': '+group.name),el('p',{},t('removalHint')),field('destination',dest),button('removeGroup',async()=>{
        try{await send('/groups/'+group.id+'/remove',{destination:dest.value});$('#dialog').close();await renderGroups();notice(t('saved'));}catch(e){notice(e.message,true);}
      }));
    },true));
    list.append(actions);
  }
  $('#content').append(list);
};

const originalEnrollment=renderEnrollment;
renderEnrollment=async function(){
  await originalEnrollment();
  const listing=el('section',{class:'card'});
  const refresh=async()=>{
    const rows=await api('/enrollments');
    listing.replaceChildren(button('refresh',()=>refresh().catch(e=>notice(e.message,true)),true),rows.length?table(['label','group','expires','used','remaining','status',''],rows.map(row=>el('tr',{},
      el('td',{},row.label),el('td',{},groups.find(g=>g.id===row.group_id)?.name||t('none')),el('td',{},date(row.expires)),
      el('td',{},row.used??t('unknown')),el('td',{},row.remaining),el('td',{},t(row.status)),
      el('td',{},row.revoked?null:button('edit',()=>tokenDialog(row),true),row.revoked?null:button('revoke',()=>{
        modal(el('h2',{},t('revoke')),el('p',{},row.label),button('revoke',async()=>{try{await send('/enrollments/'+row.id+'/revoke',{});$('#dialog').close();await refresh();notice(t('saved'));}catch(e){notice(e.message,true);}}));
      },true)) ))):empty());
  };
  $('#content').append(listing);await refresh();
};
function tokenDialog(row){
  const label=input('label','text',row.label),group=select(groupOptions(),row.group_id),hours=input('hours','number'),remaining=input('remaining','number',row.remaining);
  label.required=true;label.maxLength=100;hours.min=1;hours.max=8760;remaining.min=0;remaining.max=10000;remaining.required=true;
  modal(el('h2',{},t('edit')),el('form',{class:'form-grid',onsubmit:async event=>{
    event.preventDefault();try{await send('/enrollments/'+row.id,{label:label.value,group_id:group.value,hours:hours.value?Number(hours.value):null,remaining:Number(remaining.value)},'PUT');$('#dialog').close();await renderEnrollment();notice(t('saved'));}catch(e){notice(e.message,true);}
  }},field('label',label),field('group',group),field('renewHours',hours),field('remaining',remaining),el('button',{type:'submit'},t('save'))));
}

const originalPolicies=renderPolicies;
renderPolicies=async function(){
  await originalPolicies();enhancePasswords();
  const scope=$('#content select');if(!scope)return;
  const status=el('div',{class:'notice-inline'});scope.closest('.card').append(status);
  const update=async()=>{try{const value=await api('/password-source/'+encodeURIComponent(scope.value));status.textContent=t('passwordSource')+': '+(value.source==='client-default'?t(value.source):value.source)+'. '+t('passwordIrrecoverable');enhancePasswords();}catch(e){notice(e.message,true);}};
  scope.addEventListener('change',update);await update();
};

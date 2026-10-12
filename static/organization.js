'use strict';
Object.assign(messages,{
  organization:['Organization enrollment','ثبت سازمانی'],apiOrigin:['Public management API URL (HTTPS)','آدرس عمومی API مدیریت (HTTPS)'],
  automaticEnrollment:['Allow registration from organization installers','اجازهٔ ثبت از نصاب‌های سازمانی'],
  buildInstaller:['Download organization installer','دریافت نصاب سازمانی'],
  installerHint:['Upload a compatible managed BamdadDesk Windows client first. The installer contains a limited registration grant: distribute it only within your organization. Standard RustDesk network settings alone do not enroll devices.','ابتدا کلاینت ویندوز BamdadDesk سازگار با مدیریت را بارگذاری کنید. نصاب مجوز محدود ثبت دارد؛ فقط داخل سازمان توزیع شود. تنظیمات شبکهٔ RustDesk به‌تنهایی دستگاه را ثبت نمی‌کند.'],
  apiMigrationHint:['This address is used by new installers. Existing clients need migration support and access to the old address. Configure DNS, certificates and proxy routing separately.','این آدرس برای نصاب‌های جدید است. کلاینت‌های موجود به پشتیبانی مهاجرت و دسترسی به آدرس قدیمی نیاز دارند. DNS، گواهی و پراکسی را جداگانه تنظیم کنید.']
});
const enrollmentWithTokens=renderEnrollment;
renderEnrollment=async function(){
  await enrollmentWithTokens();
  if(user.groups!==null)return;
  const configuration=await api('/organization'),url=input('api-origin','url',configuration.api_url),automatic=input('automatic-enrollment','checkbox');
  url.required=true;automatic.checked=configuration.automatic_enrollment;
  const save=el('button',{type:'submit'},t('save'));
  $('#content').append(el('form',{class:'card form-grid',onsubmit:async e=>{e.preventDefault();save.disabled=true;try{await send('/organization',{api_url:url.value.trim(),automatic_enrollment:automatic.checked},'PUT');notice(t('saved'));}catch(err){notice(err.message,true);}finally{save.disabled=false;}}},el('h2',{},t('organization')),field('apiOrigin',url),field('automaticEnrollment',automatic),el('p',{class:'muted'},t('apiMigrationHint')),save));
  if(!can('releases.read'))return;
  const releases=await api('/releases'),release=select(releases.map(r=>[r.id,r.version])),label=input('installer-label','text','Organization'),group=select(groupOptions()),hours=input('installer-hours','number',168),uses=input('installer-uses','number',100);
  label.required=true;label.maxLength=100;hours.min=1;hours.max=8760;hours.required=true;uses.min=1;uses.max=10000;uses.required=true;release.required=true;
  const download=el('button',{type:'submit'},t('buildInstaller'));download.disabled=!releases.length;
  $('#content').append(el('form',{class:'card form-grid',onsubmit:async e=>{
    e.preventDefault();download.disabled=true;download.textContent=t('loading');
    try{
      const response=await fetch('/api/organization/installer',{method:'POST',headers:{'Content-Type':'application/json','x-csrf-token':csrf},body:JSON.stringify({label:label.value,group_id:group.value,hours:Number(hours.value),uses:Number(uses.value),release_id:release.value})});
      if(!response.ok){const error=await response.json();throw new Error(typeof error.detail==='string'?error.detail:JSON.stringify(error.detail));}
      const blob=URL.createObjectURL(await response.blob()),link=el('a',{href:blob,download:'BamdadDesk-Setup.exe'});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(blob),60000);
      await renderEnrollment();notice(t('saved'));
    }catch(err){notice(err.message,true);}finally{download.disabled=false;download.textContent=t('buildInstaller');}
  }},el('p',{class:'notice-inline'},t('installerHint')),field('version',release),field('label',label),field('group',group),field('hours',hours),field('uses',uses),download));
};

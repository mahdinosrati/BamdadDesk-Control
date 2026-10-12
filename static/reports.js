'use strict';
Object.assign(messages,{
  fromDate:['From date (UTC)','از تاریخ (UTC)'],toDate:['Through date (UTC)','تا تاریخ (UTC)'],all:['All','همه'],
  reportSearch:['Search device, peer, IP or session','جست‌وجوی دستگاه، طرف مقابل، IP یا نشست'],
  exportCsv:['Export all matching events (CSV)','خروجی تمام نتایج (CSV)'],apply:['Apply filters','اعمال فیلتر'],
  previous:['Previous','قبلی'],next:['Next','بعدی'],events:['Events','رویدادها'],
  utcHint:['Dates are Gregorian and interpreted in UTC. Duration totals use reported close events; they are not unique-session or billing totals.','تاریخ‌ها میلادی و بر اساس UTC هستند. مجموع مدت بر پایهٔ رویدادهای پایان گزارش‌شده است؛ معادل نشست‌های یکتا یا مبنای صورتحساب نیست.']
});
renderConnections=async function(){
  await fetchGroups();
  const group=select([['*',t('all')],...groupOptions()],'*');
  const device=input('report-device');device.maxLength=40;
  const start=input('start','date'),end=input('end','date'),search=input('search'),kind=select([['',t('all')],...['opened','authorized','closed'].map(k=>[k,t(k)])]);
  search.placeholder=t('reportSearch');search.maxLength=100;
  const result=el('section',{class:'card'}),summary=el('div',{class:'stats'}),pager=el('div',{class:'actions'});
  let current=1;
  const params=()=>{const p=new URLSearchParams({page:current});if(start.value)p.set('start',start.value);if(end.value)p.set('end',end.value);if(search.value)p.set('search',search.value);if(kind.value)p.set('kind',kind.value);if(group.value!=='*')p.set('group_id',group.value);if(device.value.trim())p.set('device_id',device.value.trim());return p;};
  const load=async()=>{try{const data=await api('/reports/connections?'+params());
    summary.replaceChildren(...[['events',data.summary.events],['authorized',data.summary.authorized||0],['closed',data.summary.closed||0],['duration',data.summary.duration_seconds]].map(([label,count])=>el('div',{class:'card'},t(label),el('h2',{},count))));
    result.replaceChildren(data.events.length?eventTable(data.events):empty('noData'));
    pager.replaceChildren(...[current>1?button('previous',()=>{current--;load();},true):null,el('span',{},current+' / '+data.pages),current<data.pages?button('next',()=>{current++;load();},true):null].filter(Boolean));
  }catch(e){notice(e.message,true);}};
  const filters=el('form',{class:'card form-grid',onsubmit:e=>{e.preventDefault();current=1;load();}},el('div',{class:'grid'},field('fromDate',start),field('toDate',end)),field('reportSearch',search),field('action',kind),el('div',{class:'actions'},el('button',{type:'submit'},t('apply')),button('exportCsv',()=>{
    const p=params();p.set('export','true');const link=el('a',{href:'/api/reports/connections?'+p,download:'connections.csv'});document.body.append(link);link.click();link.remove();
  },true)));
  filters.prepend(field('group',group),el('label',{},language==='fa'?'شناسهٔ مدیریتی دستگاه (اختیاری)':'Management device ID (optional)',device));
  $('#content').replaceChildren(heading('connections','connectionHint'),el('p',{class:'notice-inline'},t('utcHint')),filters,summary,result,pager);await load();
};

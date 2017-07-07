// lib/handlebars/base.js
/*jshint eqnull:true*/this.Handlebars={},function(e){e.VERSION="1.0.rc.1",e.helpers={},e.partials={},e.registerHelper=function(e,t,n){n&&(t.not=n),this.helpers[e]=t},e.registerPartial=function(e,t){this.partials[e]=t},e.registerHelper("helperMissing",function(e){if(arguments.length===2)return undefined;throw new Error("Could not find property '"+e+"'")});var t=Object.prototype.toString,n="[object Function]";e.registerHelper("blockHelperMissing",function(r,i){var s=i.inverse||function(){},o=i.fn,u="",a=t.call(r);return a===n&&(r=r.call(this)),r===!0?o(this):r===!1||r==null?s(this):a==="[object Array]"?r.length>0?e.helpers.each(r,i):s(this):o(r)}),e.K=function(){},e.createFrame=Object.create||function(t){e.K.prototype=t;var n=new e.K;return e.K.prototype=null,n},e.registerHelper("each",function(t,n){var r=n.fn,i=n.inverse,s=0,o="",u;n.data&&(u=e.createFrame(n.data));if(t&&typeof t=="object")if(t instanceof Array)for(var a=t.length;s<a;s++)u&&(u.index=s),o+=r(t[s],{data:u});else for(var f in t)t.hasOwnProperty(f)&&(u&&(u.key=f),o+=r(t[f],{data:u}),s++);return s===0&&(o=i(this)),o}),e.registerHelper("if",function(r,i){var s=t.call(r);return s===n&&(r=r.call(this)),!r||e.Utils.isEmpty(r)?i.inverse(this):i.fn(this)}),e.registerHelper("unless",function(t,n){var r=n.fn,i=n.inverse;return n.fn=i,n.inverse=r,e.helpers["if"].call(this,t,n)}),e.registerHelper("with",function(e,t){return t.fn(e)}),e.registerHelper("log",function(t){e.log(t)})}(this.Handlebars);var errorProps=["description","fileName","lineNumber","message","name","number","stack"];Handlebars.Exception=function(e){var t=Error.prototype.constructor.apply(this,arguments);for(var n=0;n<errorProps.length;n++)this[errorProps[n]]=t[errorProps[n]]},Handlebars.Exception.prototype=new Error,Handlebars.SafeString=function(e){this.string=e},Handlebars.SafeString.prototype.toString=function(){return this.string.toString()},function(){var e={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#x27;","`":"&#x60;"},t=/[&<>"'`]/g,n=/[&<>"'`]/,r=function(t){return e[t]||"&amp;"};Handlebars.Utils={escapeExpression:function(e){return e instanceof Handlebars.SafeString?e.toString():e==null||e===!1?"":n.test(e)?e.replace(t,r):e},isEmpty:function(e){return typeof e=="undefined"?!0:e===null?!0:e===!1?!0:Object.prototype.toString.call(e)==="[object Array]"&&e.length===0?!0:!1}}}(),Handlebars.VM={template:function(e){var t={escapeExpression:Handlebars.Utils.escapeExpression,invokePartial:Handlebars.VM.invokePartial,programs:[],program:function(e,t,n){var r=this.programs[e];return n?Handlebars.VM.program(t,n):r?r:(r=this.programs[e]=Handlebars.VM.program(t),r)},programWithDepth:Handlebars.VM.programWithDepth,noop:Handlebars.VM.noop};return function(n,r){return r=r||{},e.call(t,Handlebars,n,r.helpers,r.partials,r.data)}},programWithDepth:function(e,t,n){var r=Array.prototype.slice.call(arguments,2);return function(n,i){return i=i||{},e.apply(this,[n,i.data||t].concat(r))}},program:function(e,t){return function(n,r){return r=r||{},e(n,r.data||t)}},noop:function(){return""},invokePartial:function(e,t,n,r,i,s){var o={helpers:r,partials:i,data:s};if(e===undefined)throw new Handlebars.Exception("The partial "+t+" could not be found");if(e instanceof Function)return e(n,o);if(!Handlebars.compile)throw new Handlebars.Exception("The partial "+t+" could not be compiled when running in runtime-only mode");return i[t]=Handlebars.compile(e,{data:s!==undefined}),i[t](n,o)}},Handlebars.template=Handlebars.VM.template;/* QuoJS v2.3.6 - 2013/5/13
   http://quojs.tapquo.com
   Copyright (c) 2013 Javi Jimenez Villar (@soyjavi) - Licensed MIT */
(function(){var e;e=function(){var e,t,n;t=[];e=function(t,r){var i;if(!t){return n()}else if(e.toType(t)==="function"){return e(document).ready(t)}else{i=e.getDOMObject(t,r);return n(i,t)}};n=function(e,r){e=e||t;e.__proto__=n.prototype;e.selector=r||"";return e};e.extend=function(e){Array.prototype.slice.call(arguments,1).forEach(function(t){var n,r;r=[];for(n in t){r.push(e[n]=t[n])}return r});return e};n.prototype=e.fn={};return e}();window.Quo=e;"$$"in window||(window.$$=e)}).call(this);(function(){(function(e){var t,n,r,i,u,a,o,s,c,f,l;t={TYPE:"GET",MIME:"json"};r={script:"text/javascript, application/javascript",json:"application/json",xml:"application/xml, text/xml",html:"text/html",text:"text/plain"};n=0;e.ajaxSettings={type:t.TYPE,async:true,success:{},error:{},context:null,dataType:t.MIME,headers:{},xhr:function(){return new window.XMLHttpRequest},crossDomain:false,timeout:0};e.ajax=function(n){var r,o,f,h;f=e.mix(e.ajaxSettings,n);if(f.type===t.TYPE){f.url+=e.serializeParameters(f.data,"?")}else{f.data=e.serializeParameters(f.data)}if(i(f.url)){return e.jsonp(f)}h=f.xhr();h.onreadystatechange=function(){if(h.readyState===4){clearTimeout(r);return c(h,f)}};h.open(f.type,f.url,f.async);s(h,f);if(f.timeout>0){r=setTimeout(function(){return l(h,f)},f.timeout)}try{h.send(f.data)}catch(d){o=d;h=o;a("Resource not found",h,f)}if(f.async){return h}else{return u(h,f)}};e.jsonp=function(t){var r,i,u,a;if(t.async){i="jsonp"+ ++n;u=document.createElement("script");a={abort:function(){e(u).remove();if(i in window){return window[i]={}}}};r=void 0;window[i]=function(n){clearTimeout(r);e(u).remove();delete window[i];return f(n,a,t)};u.src=t.url.replace(RegExp("=\\?"),"="+i);e("head").append(u);if(t.timeout>0){r=setTimeout(function(){return l(a,t)},t.timeout)}return a}else{return console.error("QuoJS.ajax: Unable to make jsonp synchronous call.")}};e.get=function(t,n,r,i){return e.ajax({url:t,data:n,success:r,dataType:i})};e.post=function(e,t,n,r){return o("POST",e,t,n,r)};e.put=function(e,t,n,r){return o("PUT",e,t,n,r)};e["delete"]=function(e,t,n,r){return o("DELETE",e,t,n,r)};e.json=function(n,r,i){return e.ajax({url:n,data:r,success:i,dataType:t.MIME})};e.serializeParameters=function(e,t){var n,r;if(t==null){t=""}r=t;for(n in e){if(e.hasOwnProperty(n)){if(r!==t){r+="&"}r+=""+encodeURIComponent(n)+"="+encodeURIComponent(e[n])}}if(r===t){return""}else{return r}};c=function(e,t){if(e.status>=200&&e.status<300||e.status===0){if(t.async){f(u(e,t),e,t)}}else{a("QuoJS.ajax: Unsuccesful request",e,t)}};f=function(e,t,n){n.success.call(n.context,e,t)};a=function(e,t,n){n.error.call(n.context,e,t,n)};s=function(e,t){var n;if(t.contentType){t.headers["Content-Type"]=t.contentType}if(t.dataType){t.headers["Accept"]=r[t.dataType]}for(n in t.headers){e.setRequestHeader(n,t.headers[n])}};l=function(e,t){e.onreadystatechange={};e.abort();a("QuoJS.ajax: Timeout exceeded",e,t)};o=function(t,n,r,i,u){return e.ajax({type:t,url:n,data:r,success:i,dataType:u,contentType:"application/x-www-form-urlencoded"})};u=function(e,n){var r,i;i=e.responseText;if(i){if(n.dataType===t.MIME){try{i=JSON.parse(i)}catch(u){r=u;i=r;a("QuoJS.ajax: Parse Error",e,n)}}else{if(n.dataType==="xml"){i=e.responseXML}}}return i};return i=function(e){return RegExp("=\\?").test(e)}})(Quo)}).call(this);(function(){(function(e){var t,n,r,i,u,a,o,s;t=[];i=Object.prototype;r=/^\s*<(\w+|!)[^>]*>/;u=document.createElement("table");a=document.createElement("tr");n={tr:document.createElement("tbody"),tbody:u,thead:u,tfoot:u,td:a,th:a,"*":document.createElement("div")};e.toType=function(e){return i.toString.call(e).match(/\s([a-z|A-Z]+)/)[1].toLowerCase()};e.isOwnProperty=function(e,t){return i.hasOwnProperty.call(e,t)};e.getDOMObject=function(t,n){var i,u,a;i=null;u=[1,9,11];a=e.toType(t);if(a==="array"){i=o(t)}else if(a==="string"&&r.test(t)){i=e.fragment(t.trim(),RegExp.$1);t=null}else if(a==="string"){i=e.query(document,t);if(n){if(i.length===1){i=e.query(i[0],n)}else{i=e.map(function(){return e.query(i,n)})}}}else if(u.indexOf(t.nodeType)>=0||t===window){i=[t];t=null}return i};e.map=function(t,n){var r,i,u,a;a=[];r=void 0;i=void 0;if(e.toType(t)==="array"){r=0;while(r<t.length){u=n(t[r],r);if(u!=null){a.push(u)}r++}}else{for(i in t){u=n(t[i],i);if(u!=null){a.push(u)}}}return s(a)};e.each=function(t,n){var r,i;r=void 0;i=void 0;if(e.toType(t)==="array"){r=0;while(r<t.length){if(n.call(t[r],r,t[r])===false){return t}r++}}else{for(i in t){if(n.call(t[i],i,t[i])===false){return t}}}return t};e.mix=function(){var t,n,r,i,u;r={};t=0;i=arguments.length;while(t<i){n=arguments[t];for(u in n){if(e.isOwnProperty(n,u)&&n[u]!==undefined){r[u]=n[u]}}t++}return r};e.fragment=function(t,r){var i;if(r==null){r="*"}if(!(r in n)){r="*"}i=n[r];i.innerHTML=""+t;return e.each(Array.prototype.slice.call(i.childNodes),function(){return i.removeChild(this)})};e.fn.map=function(t){return e.map(this,function(e,n){return t.call(e,n,e)})};e.fn.instance=function(e){return this.map(function(){return this[e]})};e.fn.filter=function(t){return e([].filter.call(this,function(n){return n.parentNode&&e.query(n.parentNode,t).indexOf(n)>=0}))};e.fn.forEach=t.forEach;e.fn.indexOf=t.indexOf;o=function(e){return e.filter(function(e){return e!==void 0&&e!==null})};return s=function(e){if(e.length>0){return[].concat.apply([],e)}else{return e}}})(Quo)}).call(this);(function(){(function(e){e.fn.attr=function(t,n){if(this.length===0){null}if(e.toType(t)==="string"&&n===void 0){return this[0].getAttribute(t)}else{return this.each(function(){return this.setAttribute(t,n)})}};e.fn.removeAttr=function(e){return this.each(function(){return this.removeAttribute(e)})};e.fn.data=function(e,t){return this.attr("data-"+e,t)};e.fn.removeData=function(e){return this.removeAttr("data-"+e)};e.fn.val=function(t){if(e.toType(t)==="string"){return this.each(function(){return this.value=t})}else{if(this.length>0){return this[0].value}else{return null}}};e.fn.show=function(){return this.style("display","block")};e.fn.hide=function(){return this.style("display","none")};e.fn.height=function(){var e;e=this.offset();return e.height};e.fn.width=function(){var e;e=this.offset();return e.width};e.fn.offset=function(){var e;e=this[0].getBoundingClientRect();return{left:e.left+window.pageXOffset,top:e.top+window.pageYOffset,width:e.width,height:e.height}};return e.fn.remove=function(){return this.each(function(){if(this.parentNode!=null){return this.parentNode.removeChild(this)}})}})(Quo)}).call(this);(function(){(function(e){var t,n,r,i,u,a,o;r=null;t=/WebKit\/([\d.]+)/;n={Android:/(Android)\s+([\d.]+)/,ipad:/(iPad).*OS\s([\d_]+)/,iphone:/(iPhone\sOS)\s([\d_]+)/,Blackberry:/(BlackBerry|BB10|Playbook).*Version\/([\d.]+)/,FirefoxOS:/(Mozilla).*Mobile[^\/]*\/([\d\.]*)/,webOS:/(webOS|hpwOS)[\s\/]([\d.]+)/};e.isMobile=function(){r=r||u();return r.isMobile&&r.os.name!=="firefoxOS"};e.environment=function(){r=r||u();return r};e.isOnline=function(){return navigator.onLine};u=function(){var e,t;t=navigator.userAgent;e={};e.browser=i(t);e.os=a(t);e.isMobile=!!e.os;e.screen=o();return e};i=function(e){var n;n=e.match(t);if(n){return n[0]}else{return e}};a=function(e){var t,r,i;t=null;for(r in n){i=e.match(n[r]);if(i){t={name:r==="iphone"||r==="ipad"?"ios":r,version:i[2].replace("_",".")};break}}return t};return o=function(){return{width:window.innerWidth,height:window.innerHeight}}})(Quo)}).call(this);(function(){(function(e){var t,n,r,i,u,a,o,s,c,f,l,h;t=1;i={};r={preventDefault:"isDefaultPrevented",stopImmediatePropagation:"isImmediatePropagationStopped",stopPropagation:"isPropagationStopped"};n={touchstart:"mousedown",touchmove:"mousemove",touchend:"mouseup",touch:"click",doubletap:"dblclick",orientationchange:"resize"};u=/complete|loaded|interactive/;e.fn.on=function(t,n,r){if(n==="undefined"||e.toType(n)==="function"){return this.bind(t,n)}else{return this.delegate(n,t,r)}};e.fn.off=function(t,n,r){if(n==="undefined"||e.toType(n)==="function"){return this.unbind(t,n)}else{return this.undelegate(n,t,r)}};e.fn.ready=function(t){if(u.test(document.readyState)){return t(e)}else{return e.fn.addEvent(document,"DOMContentLoaded",function(){return t(e)})}};e.Event=function(e,t){var n,r;n=document.createEvent("Events");n.initEvent(e,true,true,null,null,null,null,null,null,null,null,null,null,null,null);if(t){for(r in t){n[r]=t[r]}}return n};e.fn.bind=function(e,t){return this.each(function(){l(this,e,t)})};e.fn.unbind=function(e,t){return this.each(function(){h(this,e,t)})};e.fn.delegate=function(t,n,r){return this.each(function(i,u){l(u,n,r,t,function(n){return function(r){var i,o;o=e(r.target).closest(t,u).get(0);if(o){i=e.extend(a(r),{currentTarget:o,liveFired:u});return n.apply(o,[i].concat([].slice.call(arguments,1)))}}})})};e.fn.undelegate=function(e,t,n){return this.each(function(){h(this,t,n,e)})};e.fn.trigger=function(t,n,r){if(e.toType(t)==="string"){t=e.Event(t,n)}if(r!=null){t.originalEvent=r}return this.each(function(){this.dispatchEvent(t)})};e.fn.addEvent=function(e,t,n){if(e.addEventListener){return e.addEventListener(t,n,false)}else if(e.attachEvent){return e.attachEvent("on"+t,n)}else{return e["on"+t]=n}};e.fn.removeEvent=function(e,t,n){if(e.removeEventListener){return e.removeEventListener(t,n,false)}else if(e.detachEvent){return e.detachEvent("on"+t,n)}else{return e["on"+t]=null}};l=function(t,n,r,u,a){var c,l,h,d;n=s(n);h=f(t);l=i[h]||(i[h]=[]);c=a&&a(r,n);d={event:n,callback:r,selector:u,proxy:o(c,r,t),delegate:c,index:l.length};l.push(d);return e.fn.addEvent(t,d.event,d.proxy)};h=function(t,n,r,u){var a;n=s(n);a=f(t);return c(a,n,r,u).forEach(function(n){delete i[a][n.index];return e.fn.removeEvent(t,n.event,n.proxy)})};f=function(e){return e._id||(e._id=t++)};s=function(t){var r;r=e.isMobile()?t:n[t];return r||t};o=function(e,t,n){var r;t=e||t;r=function(e){var r;r=t.apply(n,[e].concat(e.data));if(r===false){e.preventDefault()}return r};return r};c=function(e,t,n,r){return(i[e]||[]).filter(function(e){return e&&(!t||e.event===t)&&(!n||e.callback===n)&&(!r||e.selector===r)})};return a=function(t){var n;n=e.extend({originalEvent:t},t);e.each(r,function(e,r){n[e]=function(){this[r]=function(){return true};return t[e].apply(t,arguments)};return n[r]=function(){return false}});return n}})(Quo)}).call(this);(function(){(function($$){var CURRENT_TOUCH,EVENT,FIRST_TOUCH,GESTURE,GESTURES,HOLD_DELAY,TAPS,TOUCH_TIMEOUT,_angle,_capturePinch,_captureRotation,_cleanGesture,_distance,_fingersPosition,_getTouches,_hold,_isSwipe,_listenTouches,_onTouchEnd,_onTouchMove,_onTouchStart,_parentIfText,_swipeDirection,_trigger;TAPS=null;EVENT=void 0;GESTURE={};FIRST_TOUCH=[];CURRENT_TOUCH=[];TOUCH_TIMEOUT=void 0;HOLD_DELAY=650;GESTURES=["touch","tap","singleTap","doubleTap","hold","swipe","swiping","swipeLeft","swipeRight","swipeUp","swipeDown","rotate","rotating","rotateLeft","rotateRight","pinch","pinching","pinchIn","pinchOut","drag","dragLeft","dragRight","dragUp","dragDown"];GESTURES.forEach(function(e){$$.fn[e]=function(t){var n;n=e==="touch"?"touchend":e;return $$(document.body).delegate(this.selector,n,t)};return this});$$(document).ready(function(){return _listenTouches()});_listenTouches=function(){var e;e=$$(document.body);e.bind("touchstart",_onTouchStart);e.bind("touchmove",_onTouchMove);e.bind("touchend",_onTouchEnd);return e.bind("touchcancel",_cleanGesture)};_onTouchStart=function(e){var t,n,r,i;EVENT=e;r=Date.now();t=r-(GESTURE.last||r);TOUCH_TIMEOUT&&clearTimeout(TOUCH_TIMEOUT);i=_getTouches(e);n=i.length;FIRST_TOUCH=_fingersPosition(i,n);GESTURE.el=$$(_parentIfText(i[0].target));GESTURE.fingers=n;GESTURE.last=r;if(!GESTURE.taps){GESTURE.taps=0}GESTURE.taps++;if(n===1){if(n>=1){GESTURE.gap=t>0&&t<=250}return setTimeout(_hold,HOLD_DELAY)}else if(n===2){GESTURE.initial_angle=parseInt(_angle(FIRST_TOUCH),10);GESTURE.initial_distance=parseInt(_distance(FIRST_TOUCH),10);GESTURE.angle_difference=0;return GESTURE.distance_difference=0}};_onTouchMove=function(e){var t,n,r;EVENT=e;if(GESTURE.el){r=_getTouches(e);t=r.length;if(t===GESTURE.fingers){CURRENT_TOUCH=_fingersPosition(r,t);n=_isSwipe(e);if(n){GESTURE.prevSwipe=true}if(n||GESTURE.prevSwipe===true){_trigger("swiping")}if(t===2){_captureRotation();_capturePinch();e.preventDefault()}}else{_cleanGesture()}}return true};_isSwipe=function(e){var t,n,r;t=false;if(CURRENT_TOUCH[0]){n=Math.abs(FIRST_TOUCH[0].x-CURRENT_TOUCH[0].x)>30;r=Math.abs(FIRST_TOUCH[0].y-CURRENT_TOUCH[0].y)>30;t=GESTURE.el&&(n||r)}return t};_onTouchEnd=function(e){var t,n,r,i,u;EVENT=e;_trigger("touch");if(GESTURE.fingers===1){if(GESTURE.taps===2&&GESTURE.gap){_trigger("doubleTap");_cleanGesture()}else if(_isSwipe()||GESTURE.prevSwipe){_trigger("swipe");u=_swipeDirection(FIRST_TOUCH[0].x,CURRENT_TOUCH[0].x,FIRST_TOUCH[0].y,CURRENT_TOUCH[0].y);_trigger("swipe"+u);_cleanGesture()}else{_trigger("tap");if(GESTURE.taps===1){TOUCH_TIMEOUT=setTimeout(function(){_trigger("singleTap");return _cleanGesture()},100)}}}else{t=false;if(GESTURE.angle_difference!==0){_trigger("rotate",{angle:GESTURE.angle_difference});i=GESTURE.angle_difference>0?"rotateRight":"rotateLeft";_trigger(i,{angle:GESTURE.angle_difference});t=true}if(GESTURE.distance_difference!==0){_trigger("pinch",{angle:GESTURE.distance_difference});r=GESTURE.distance_difference>0?"pinchOut":"pinchIn";_trigger(r,{distance:GESTURE.distance_difference});t=true}if(!t&&CURRENT_TOUCH[0]){if(Math.abs(FIRST_TOUCH[0].x-CURRENT_TOUCH[0].x)>10||Math.abs(FIRST_TOUCH[0].y-CURRENT_TOUCH[0].y)>10){_trigger("drag");n=_swipeDirection(FIRST_TOUCH[0].x,CURRENT_TOUCH[0].x,FIRST_TOUCH[0].y,CURRENT_TOUCH[0].y);_trigger("drag"+n)}}_cleanGesture()}return EVENT=void 0};_fingersPosition=function(e,t){var n,r;r=[];n=0;e=e[0].targetTouches?e[0].targetTouches:e;while(n<t){r.push({x:e[n].pageX,y:e[n].pageY});n++}return r};_captureRotation=function(){var angle,diff,i,symbol;angle=parseInt(_angle(CURRENT_TOUCH),10);diff=parseInt(GESTURE.initial_angle-angle,10);if(Math.abs(diff)>20||GESTURE.angle_difference!==0){i=0;symbol=GESTURE.angle_difference<0?"-":"+";while(Math.abs(diff-GESTURE.angle_difference)>90&&i++<10){eval("diff "+symbol+"= 180;")}GESTURE.angle_difference=parseInt(diff,10);return _trigger("rotating",{angle:GESTURE.angle_difference})}};_capturePinch=function(){var e,t;t=parseInt(_distance(CURRENT_TOUCH),10);e=GESTURE.initial_distance-t;if(Math.abs(e)>10){GESTURE.distance_difference=e;return _trigger("pinching",{distance:e})}};_trigger=function(e,t){if(GESTURE.el){t=t||{};if(CURRENT_TOUCH[0]){t.iniTouch=GESTURE.fingers>1?FIRST_TOUCH:FIRST_TOUCH[0];t.currentTouch=GESTURE.fingers>1?CURRENT_TOUCH:CURRENT_TOUCH[0]}return GESTURE.el.trigger(e,t,EVENT)}};_cleanGesture=function(e){FIRST_TOUCH=[];CURRENT_TOUCH=[];GESTURE={};return clearTimeout(TOUCH_TIMEOUT)};_angle=function(e){var t,n,r;t=e[0];n=e[1];r=Math.atan((n.y-t.y)*-1/(n.x-t.x))*(180/Math.PI);if(r<0){return r+180}else{return r}};_distance=function(e){var t,n;t=e[0];n=e[1];return Math.sqrt((n.x-t.x)*(n.x-t.x)+(n.y-t.y)*(n.y-t.y))*-1};_getTouches=function(e){if($$.isMobile()){return e.touches}else{return[e]}};_parentIfText=function(e){if("tagName"in e){return e}else{return e.parentNode}};_swipeDirection=function(e,t,n,r){var i,u;i=Math.abs(e-t);u=Math.abs(n-r);if(i>=u){if(e-t>0){return"Left"}else{return"Right"}}else{if(n-r>0){return"Up"}else{return"Down"}}};return _hold=function(){if(GESTURE.last&&Date.now()-GESTURE.last>=HOLD_DELAY){_trigger("hold");return GESTURE.taps=0}}})(Quo)}).call(this);(function(){(function(e){e.fn.text=function(t){if(t||e.toType(t)==="number"){return this.each(function(){return this.textContent=t})}else{return this[0].textContent}};e.fn.html=function(t){var n;n=e.toType(t);if(t||n==="number"||n==="string"){return this.each(function(){var e,r,i,u;if(n==="string"||n==="number"){return this.innerHTML=t}else{this.innerHTML=null;if(n==="array"){u=[];for(r=0,i=t.length;r<i;r++){e=t[r];u.push(this.appendChild(e))}return u}else{return this.appendChild(t)}}})}else{return this[0].innerHTML}};e.fn.append=function(t){var n;n=e.toType(t);return this.each(function(){var e=this;if(n==="string"){return this.insertAdjacentHTML("beforeend",t)}else if(n==="array"){return t.each(function(t,n){return e.appendChild(n)})}else{return this.appendChild(t)}})};e.fn.prepend=function(t){var n;n=e.toType(t);return this.each(function(){var e=this;if(n==="string"){return this.insertAdjacentHTML("afterbegin",t)}else if(n==="array"){return t.each(function(t,n){return e.insertBefore(n,e.firstChild)})}else{return this.insertBefore(t,this.firstChild)}})};e.fn.replaceWith=function(t){var n;n=e.toType(t);this.each(function(){var e=this;if(this.parentNode){if(n==="string"){return this.insertAdjacentHTML("beforeBegin",t)}else if(n==="array"){return t.each(function(t,n){return e.parentNode.insertBefore(n,e)})}else{return this.parentNode.insertBefore(t,this)}}});return this.remove()};return e.fn.empty=function(){return this.each(function(){return this.innerHTML=null})}})(Quo)}).call(this);(function(){(function(e){var t,n,r,i,u,a;r="parentNode";t=/^\.([\w-]+)$/;n=/^#[\w\d-]+$/;i=/^[\w-]+$/;e.query=function(e,r){var u;r=r.trim();if(t.test(r)){u=e.getElementsByClassName(r.replace(".",""))}else if(i.test(r)){u=e.getElementsByTagName(r)}else if(n.test(r)&&e===document){u=e.getElementById(r.replace("#",""));if(!u){u=[]}}else{u=e.querySelectorAll(r)}if(u.nodeType){return[u]}else{return Array.prototype.slice.call(u)}};e.fn.find=function(t){var n;if(this.length===1){n=Quo.query(this[0],t)}else{n=this.map(function(){return Quo.query(this,t)})}return e(n)};e.fn.parent=function(e){var t;t=e?a(this):this.instance(r);return u(t,e)};e.fn.siblings=function(e){var t;t=this.map(function(e,t){return Array.prototype.slice.call(t.parentNode.children).filter(function(e){return e!==t})});return u(t,e)};e.fn.children=function(e){var t;t=this.map(function(){return Array.prototype.slice.call(this.children)});return u(t,e)};e.fn.get=function(e){if(e===undefined){return this}else{return this[e]}};e.fn.first=function(){return e(this[0])};e.fn.last=function(){return e(this[this.length-1])};e.fn.closest=function(t,n){var r,i;i=this[0];r=e(t);if(!r.length){i=null}while(i&&r.indexOf(i)<0){i=i!==n&&i!==document&&i.parentNode}return e(i)};e.fn.each=function(e){this.forEach(function(t,n){return e.call(t,n,t)});return this};a=function(t){var n;n=[];while(t.length>0){t=e.map(t,function(e){if((e=e.parentNode)&&e!==document&&n.indexOf(e)<0){n.push(e);return e}})}return n};return u=function(t,n){if(n===undefined){return e(t)}else{return e(t).filter(n)}}})(Quo)}).call(this);(function(){(function(e){var t,n,r;t=["-webkit-","-moz-","-ms-","-o-",""];e.fn.addClass=function(e){return this.each(function(){if(!r(e,this.className)){this.className+=" "+e;return this.className=this.className.trim()}})};e.fn.removeClass=function(e){return this.each(function(){if(!e){return this.className=""}else{if(r(e,this.className)){return this.className=this.className.replace(e," ").replace(/\s+/g," ").trim()}}})};e.fn.toggleClass=function(e){return this.each(function(){if(r(e,this.className)){return this.className=this.className.replace(e," ")}else{this.className+=" "+e;return this.className=this.className.trim()}})};e.fn.hasClass=function(e){return r(e,this[0].className)};e.fn.style=function(e,t){if(t){return this.each(function(){return this.style[e]=t})}else{return this[0].style[e]||n(this[0],e)}};e.fn.css=function(e,t){return this.style(e,t)};e.fn.vendor=function(e,n){var r,i,u,a;a=[];for(i=0,u=t.length;i<u;i++){r=t[i];a.push(this.style(""+r+e,n))}return a};r=function(e,t){var n;n=t.split(/\s+/g);return n.indexOf(e)>=0};return n=function(e,t){return document.defaultView.getComputedStyle(e,"")[t]}})(Quo)}).call(this);(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['infoPanel'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "<div id=\"cb-status-left\" class=\"cb-control cb-status-left\" data-action=\"close\">\r\n	<div id=\"cb-info-panel\">\r\n		<div class=\"info-text\">None!</div>\r\n	</div>\r\n</div>\r\n";
  });
templates['loadingOverlay'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\r\n<div id=\"cb-loading-overlay\" class=\"cb-control\"></div>\r\n";
  });
templates['navigateLeft'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\r\n<div data-trigger=\"click\" data-action=\"navigation\" data-navigate-side=\"left\" class=\"cb-control navigate navigate-left \">\r\n	<span class=\"icon-arrow-left\"></span>\r\n</div>\r\n";
  });
templates['navigateRight'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\r\n<div data-trigger=\"click\" data-action=\"navigation\" data-navigate-side=\"right\" class=\"cb-control navigate navigate-right\">\r\n	<span class=\"icon-arrow-right\"></span>\r\n</div>\r\n";
  });
templates['progressbar'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "<div id=\"cb-status-right\" class=\"cb-control cb-status-right\" data-action=\"close\">\r\n	<div id=\"cb-progress-bar\">\r\n		<div class=\"progressbar-value\"></div>\r\n	</div>\r\n	<div class=\"progressbar-text\">None!</div>\r\n</div>\r\n";
  });
templates['thumbnails'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\n<div class=\"cb-control thumbnails\"></div>\n";
  });
templates['toggleMode'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\r\n<div data-trigger=\"click\" data-action=\"navigation\" data-navigate-side=\"bottom\" class=\"cb-control navigate navigate-center-bottom\">\r\n	<span class=\"icon-spinner\"></span>\r\n</div>\r\n";
  });
templates['toggleToolbar'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\r\n<div data-trigger=\"click\" data-action=\"navigation\" data-navigate-side=\"center\" class=\"cb-control navigate navigate-center-top\">\r\n	<span class=\"icon-open-toolbar\"></span>\r\n</div>\r\n";
  });
templates['toolbar'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [2,'>= 1.0.0-rc.3'];
helpers = helpers || Handlebars.helpers; data = data || {};
  


  return "\n<div class=\"toolbar\">\n\n	<ul class=\"pull-left\">\n		<li class=\"close\">\n			<button data-trigger=\"click\" data-action=\"close\" title=\"close\" class=\"icon-remove-sign\"></button>\n		</li>\n		<li class=\"close separator\"></li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"zoomOut\" title=\"Zoom out\" class=\"icon-zoom-out\"></button>\n		</li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"zoomIn\" title=\"Zoom in\" class=\"icon-zoom-in\"></button>\n		</li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"fitWidth\" title=\"Fit page to window width\" class=\"icon-expand\"></button>\n		</li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"originalSize\" title=\"Do not scale image\" class=\"icon-expand-2\"></button>\n		</li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"fitWindow\" title=\"Fit page to window\" class=\"icon-contract\"></button>\n		</li>\n		<li>\n			<button data-trigger=\"click\" data-action=\"toggleReadingMode\" title=\"switch reading direction\" class=\"icon-arrow-right-3 manga-false\"></button>\n			<button data-trigger=\"click\" data-action=\"toggleReadingMode\" title=\"switch reading direction\" class=\"icon-arrow-left-3 manga-true\"></button>\n		</li>\n	</ul>\n\n	<ul class=\"pull-right\">\n		<li>\n			<button data-trigger=\"click\" data-action=\"thumbs\" title=\"Show Thumbnails\" class=\"icon-image\"></button>\n		</li>\n		<li><span id=\"current-page\"></span> / <span id=\"page-count\"></span></li>\n	</ul>\n\n</div>\n";
  });
})();/* exported ComicBook */


var ComicBook = (function ($) {

	'use strict';

	/**
	 * Merge two arrays. Any properties in b will replace the same properties in
	 * a. New properties from b will be added to a.
	 *
	 * @param a {Object}
	 * @param b {Object}
	 */
	function merge(a, b) {

		var prop;

		if (typeof b === 'undefined') { b = {}; }

		for (prop in a) {
			if (a.hasOwnProperty(prop)) {
				if (prop in b) { continue; }
				b[prop] = a[prop];
			}
		}

		return b;
	}

	/**
	 * Exception class. Always throw an instance of this when throwing exceptions.
	 *
	 * @param {String} type
	 * @param {Object} object
	 * @returns {ComicBookException}
	 */
	var ComicBookException = {
		INVALID_ACTION: 'invalid action',
		INVALID_PAGE: 'invalid page',
		INVALID_PAGE_TYPE: 'invalid page type',
		UNDEFINED_CONTROL: 'undefined control',
		INVALID_ZOOM_MODE: 'invalid zoom mode',
		INVALID_NAVIGATION_EVENT: 'invalid navigation event'
	};

	function ComicBook(id, srcs, opts) {

		var self = this;
		var canvas_container_id = id;   // canvas element id
		this.srcs = srcs; // array of image srcs for pages

		var defaults = {
			zoomMode: 'smart', // manual / originalSize / fitWidth / fitWindow
			manga: false,     // true / false
			enhance: {},
			keyboard: {
				// next: 78,
				next: 39,
				// previous: 80,
				previous: 37,
				toggleLayout: 76,
				thumbnails: 84
			},
			libPath: '/comicbook/js/',
			forward_buffer: 3,
			fileName: null
		};

		// Possible zoom modes that are cycled through when you hit the cycle-zoom-mode button
		// TODO: Add "smart" zoom mode that looks at aspect ratio and reading direction, to make two-page splits display in a sane matter.
		var zoomModes = ['smart', 'originalSize', 'fitWindow'];
		// 'manual' is disabled because you enter it by clicking the zoom buttons, 'fitWidth' is disabled because I never use it.

		this.showUi = false;
		this.isMobile = false;

		// mobile enhancements
		if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile/i.test(navigator.userAgent)) {

			this.isMobile = true;
			document.body.classList.add('mobile');



			window.addEventListener('load', function () {
				setTimeout(function () {
					window.scrollTo(0, 1);
				}, 0);
			});
		}

		var options = merge(defaults, opts); // options array for internal use

		console.log('Passed opts =', opts);
		console.log('Overall Options =', options);

		var no_pages = srcs.length;
		var pages = [];                 // array of preloaded Image objects
		var canvas_container;           // the HTML5 canvas container object
		var canvases = [];              // the HTML5 canvas objects
		var loaded = [];                // the images that have been loaded so far
		var scale = 1;                  // page zoom scale, 1 = 100%
		var is_double_page_spread = false;
		var controlsRendered = false;   // have the user controls been inserted into the dom yet?
		var page_requested = false;     // used to request non preloaded pages
		var shiv = false;

		var smartActualSize = false;    // Once the smart-sizer has triggered into actual-size mode, it need to be sticky.

		/**
		 * Gets the window.innerWidth - scrollbars
		 */
		function windowWidth() {

			var height = window.innerHeight + 1;

			if (shiv === false) {
				shiv = $(document.createElement('div'))
					.attr('id', 'cb-width-shiv')
					.css({
						width: '100%',
						position: 'absolute',
						top: 0,
						zIndex: '-1000'
					});

				$('body').append(shiv);
			}

			shiv.height(height);

			return shiv.innerWidth();
		}

		// the current page
		var pointer = 0;

		/**
		 * Setup the canvas element for use throughout the class.
		 *
		 * @see #ComicBook.prototype.draw
		 * @see #ComicBook.prototype.enhance
		 */
		function init() {

			// setup canvas
			canvas_container = $(document.getElementById(canvas_container_id));

			// render user controls
			if (controlsRendered === false) {
				self.renderControls();
				controlsRendered = true;
			}

			// add page controls
			window.addEventListener('keydown', self.navigation, false);

		}

		window.addEventListener('touchstart', function (e) {
			var $el = $(e.target);
			if ($el.attr('id') === 'comic') {
				self.toggleUIOverlay();
			}
			if ($el.data('toggle') === 'dropdown' ) {
				$el.siblings('.dropdown').toggle();
			}
		}, false);

		/**
		 * Render Handlebars templates. Templates with data-trigger & data-action will
		 * have the specified events bound.
		 */
		ComicBook.prototype.renderControls = function () {

			var controls = {}, $toolbar;

			$.each(Handlebars.templates, function (name, template) {

				var $template = $(template().trim());
				controls[name] = $template;

				// add event listeners to controls that specify callbacks
				$template.find('*').andSelf().filter('[data-action][data-trigger]').each(function () {

					var $this = $(this);
					var trigger = $this.data('trigger');
					var action = $this.data('action');

					// trigger a direct method if exists
					if (typeof self[$this.data('action')] === 'function') {
						$this.on(trigger, self[action]);
					}

					// throw an event to be caught outside if the app code
					$this.on(trigger, function (e) {
						$(self).trigger(trigger, e);
					});
				});

				$(canvas_container).before($template);
			});

			this.controls = controls;

			$toolbar = this.getControl('toolbar');
			$toolbar
				.find('.manga-' + options.manga).show().end()
				.find('.manga-' + !options.manga).hide().end()
				.find('.layout').hide().end();

		};

		ComicBook.prototype.getControl = function (control) {
			if (typeof this.controls[control] !== 'object') {
				throw ComicBookException.UNDEFINED_CONTROL + ' ' + control;
			}
			return this.controls[control];
		};

		ComicBook.prototype.showControl = function (control) {
			this.getControl(control).show().addClass('open');
		};

		ComicBook.prototype.hideControl = function (control) {
			this.getControl(control).removeClass('open').hide();
		};

		ComicBook.prototype.hideToolBar = function () {
			this.getControl('toolbar').toggle(false);
			$('#cb-status-right').hide();
			$('#cb-status-left').hide();

		};

		ComicBook.prototype.toggleControl = function (control) {

			this.getControl(control).toggle().toggleClass('open');

		};

		ComicBook.prototype.toggleLayout = function() {

			var $toolbar = self.getControl('toolbar');

			$toolbar.find('.layout').hide().end();

			self.drawPage();
		};

		/**
		 * Get the image for a given page.
		 *
		 * @return Image
		 */
		ComicBook.prototype.getPage = function (i)
		{

			if (i < 0 || i > srcs.length-1) {
				throw ComicBookException.INVALID_PAGE + ' ' + i;
			}

			if (typeof pages[i] === 'object') {
				return pages[i];
			} else {
				page_requested = i;
				this.showControl('loadingOverlay');
			}
		};

		/**
		 * @see #preload
		 */
		ComicBook.prototype.draw = function () {

			init();
			// resize navigation controls
			// $('.navigate').outerHeight(window.innerHeight);
			$('#cb-loading-overlay').outerWidth(windowWidth()).height(window.innerHeight);

			// preload images if needed
			if (pages.length !== no_pages) {
				this.preload();
			} else {
				this.drawPage();
				this.updateInfoPanel();
			}
		};

		/**
		 * Zoom the canvas
		 *
		 * @param new_scale {Number} Scale the canvas to this ratio
		 */
		ComicBook.prototype.zoom = function (new_scale) {
			options.zoomMode = 'manual';
			scale = new_scale;
			if (typeof this.getPage(pointer) === 'object')
			{
				this.drawPage();
			}
		};

		ComicBook.prototype.zoomIn = function () {
			self.zoom(scale + 0.1);
		};

		ComicBook.prototype.zoomOut = function () {
			self.zoom(scale - 0.1);
		};

		ComicBook.prototype.fitWidth = function () {
			options.zoomMode = 'fitWidth';
			self.drawPage();
		};

		ComicBook.prototype.originalSize = function () {
			options.zoomMode = 'originalSize';
			self.drawPage();
		};

		ComicBook.prototype.fitWindow = function () {
			options.zoomMode = 'fitWindow';
			self.drawPage();
		};
		ComicBook.prototype.thumbs = function () {
			self.toggleThumbnails();
		};

		/**
		 * Preload all images, draw the page only after a given number have been loaded.
		 *
		 * @see #drawPage
		 */
		ComicBook.prototype.preload = function () {

			var i = pointer; // the current page counter for this method
			var rendered = false;
			var queue = [];

			this.showControl('loadingOverlay');

			function loadImage(i) {

				var page = new Image();
				page.src = srcs[i];

				page.onload = function () {

					pages[i] = this;
					loaded.push(i);

					// There is a  wierd bug here where loaded has two "0" elements at the beginning of the array,
					// leading to loaded.length being one too large. If I block insertion of duplicate elements,
					// nothing ever loads, so fukkit, just subtracting one for the moment.

					$('#cb-progress-bar .progressbar-value').css('width', Math.floor(((loaded.length-1) / no_pages) * 100) + '%');
					$('.progressbar-text').text('Loaded ' + String(loaded.length-1) + ' of ' + String(no_pages));


					// start rendering the comic when the requested page is ready
					if ((rendered === false && ($.inArray(pointer, loaded) !== -1) ||
							(typeof page_requested === 'number' && $.inArray(page_requested, loaded) !== -1))
					) {
						// if the user is waiting for a page to be loaded, render that one instead of the default pointer
						if (typeof page_requested === 'number') {
							pointer = page_requested-1;
							page_requested = false;
						}

						self.drawPage();
						self.hideControl('loadingOverlay');
						rendered = true;
					}

					if (queue.length) {
						loadImage(queue[0]);
						queue.splice(0,1);
					} else {
						$('#cb-status-right').delay(500).fadeOut();
						$('#cb-status-left').delay(500).fadeOut();
					}


				};

			}

			// loads pages in both directions so you don't have to wait for all pages
			// to be loaded before you can scroll backwards
			function preload(start, stop) {

				var j = 0;
				var count = 1;
				var forward = start;
				var backward = start-1;

				while (forward <= stop) {

					if (count > options.forward_buffer && backward > -1) {
						queue.push(backward);
						backward--;
						count = 0;
					} else {
						queue.push(forward);
						forward++;
					}
					count++;
				}

				while (backward > -1) {
					queue.push(backward);
					backward--;
				}

				loadImage(queue[j]);
			}

			preload(i, srcs.length-1);
		};

		ComicBook.prototype.updateInfoPanel = function ()
		{
			var bubbleText = '';
			if (options.fileName)
			{
				bubbleText += 'File: ' + options.fileName + '<br>';
			}

			// ['smart', 'originalSize', 'fitWindow'];
			if (options.zoomMode === 'smart')
			{
				bubbleText += 'Zoom Mode: Smart<br>';
			}
			else if (options.zoomMode === 'originalSize')
			{
				bubbleText += 'Zoom Mode: Original Size<br>';
			}
			else if (options.zoomMode === 'fitWindow')
			{
				bubbleText += 'Zoom Mode: Fit Window<br>';
			}
			else if (options.zoomMode === 'manual')
			{
				bubbleText += 'Zoom Mode: Manual<br>';
			}
			else
			{
				bubbleText += 'Zoom Mode: Unknown?<br>';
			}

			var page = self.getPage(pointer);
			if (page)
			{
				bubbleText += 'Image Size: ' + page.width + 'x' + page.height + '<br>';
			}
			else
			{
				bubbleText += 'Images loading!<br>';
			}

			$('.info-text').html(bubbleText);

		};


		ComicBook.prototype.pageLoaded = function (page_no) {

			return (typeof loaded[page_no-1] !== 'undefined');
		};

		/**
		 * Draw the current page in the canvas
		 */
		ComicBook.prototype.drawPage = function(page_no, reset_scroll) {

			var scrollY;

			reset_scroll = (typeof reset_scroll !== 'undefined') ? reset_scroll : true;
			scrollY = reset_scroll ? 0 : window.scrollY;

			// if a specific page is given try to render it, if not bail and wait for preload() to render it
			if (typeof page_no === 'number' && page_no < srcs.length && page_no > 0) {
				pointer = page_no-1;
				if (!this.pageLoaded(page_no)) {
					this.showControl('loadingOverlay');
					return;
				}
			}

			if (pointer < 0) { pointer = 0; }

			var zoom_scale;
			var offsetW = 0;

			var page = self.getPage(pointer);
			var page2 = false;

			if (typeof page !== 'object') {
				throw ComicBookException.INVALID_PAGE_TYPE + ' ' + typeof page;
			}

			var width = page.width, height = page.height;

			var width_scale;
			var windowHeight;
			var height_scale;


			// update the page scale if a non manual mode has been chosen
			switch (options.zoomMode) {

			case 'manual':
				document.body.style.overflowX = 'auto';
				zoom_scale = scale;
				break;

			case 'fitWidth':
				document.body.style.overflowX = 'hidden';

				// scale up if the window is wider than the page, scale down if the window
				// is narrower than the page
				zoom_scale = (windowWidth() > width) ? ((windowWidth() - width) / windowWidth()) + 1 : windowWidth() / width;

				// update the interal scale var so switching zoomModes while zooming will be smooth
				scale = zoom_scale;
				break;

			case 'originalSize':
				document.body.style.overflowX = 'auto';
				zoom_scale = 1;
				scale = zoom_scale;
				break;

			case 'fitWindow':
				document.body.style.overflowX = 'hidden';

				width_scale = (windowWidth() > width) ?
					((windowWidth() - width) / windowWidth()) + 1 // scale up if the window is wider than the page
					: windowWidth() / width; // scale down if the window is narrower than the page
				windowHeight = window.innerHeight;
				height_scale = (windowHeight > height) ?
					((windowHeight - height) / windowHeight) + 1 // scale up if the window is wider than the page
					: windowHeight / height; // scale down if the window is narrower than the page

				zoom_scale = (width_scale > height_scale) ? height_scale : width_scale;
				scale = zoom_scale;
				break;


			case 'smart':

				// Fit to window if page has an aspect ratio smaller then 2.5.
				// Otherwise, show original size.

				if ((height / width) > 2.5 )
				{
					smartActualSize = true;
				}
				if (smartActualSize)
				{
					document.body.style.overflowX = 'auto';
					zoom_scale = 1;
					scale = zoom_scale;
				}
				else
				{
					document.body.style.overflowX = 'hidden';

					width_scale = (windowWidth() > width) ?
						((windowWidth() - width) / windowWidth()) + 1 // scale up if the window is wider than the page
						: windowWidth() / width; // scale down if the window is narrower than the page
					windowHeight = window.innerHeight;
					height_scale = (windowHeight > height) ?
						((windowHeight - height) / windowHeight) + 1 // scale up if the window is wider than the page
						: windowHeight / height; // scale down if the window is narrower than the page

					zoom_scale = (width_scale > height_scale) ? height_scale : width_scale;
					scale = zoom_scale;
				}
				break;

			default:
				throw ComicBookException.INVALID_ZOOM_MODE + ' ' + options.zoomMode;
			}


			var canvas_width  = page.width * zoom_scale;
			var canvas_height = page.height * zoom_scale;

			var page_width = (options.zoomMode === 'manual') ? page.width * scale : canvas_width;
			var page_height = (options.zoomMode === 'manual') ? page.height * scale : canvas_height;

			canvas_height = page_height;


			// always keep pages centered
			if (canvas_width < windowWidth()) {
				offsetW = (windowWidth() - page_width) / 2;
			}

			// draw the page(s)
			this.drawImageToCanvasArray(page, offsetW, page_width, page_height);

			var current_page = pointer + 1;

			this.getControl('toolbar')
				.find('#current-page').text(current_page)
				.end()
				.find('#page-count').text(srcs.length);



			// disable the fit width button if needed
			$('button.cb-fit-width').attr('disabled', (options.zoomMode === 'fitWidth'));
			$('button.cb-fit-window').attr('disabled', (options.zoomMode === 'fitWindow'));

			// disable prev/next buttons if not needed
			$('.navigate').show();
			if (pointer === 0) {
				if (options.manga) {
					$('.navigate-left').show();
					$('.navigate-right').hide();
				} else {
					$('.navigate-left').hide();
					$('.navigate-right').show();
				}
			}

			if (pointer === srcs.length-1 || (typeof page2 === 'object' && pointer === srcs.length-2)) {
				if (options.manga) {
					$('.navigate-left').hide();
					$('.navigate-right').show();
				} else {
					$('.navigate-left').show();
					$('.navigate-right').hide();
				}
			}

			this.updateInfoPanel();

		};



		ComicBook.prototype.drawImageToCanvasArray = function (image, offsetW, page_width, page_height) {

			var maxDrawHeight = 1500;
			var runningHeight = page_height;
			var xOffset = 0;
			var chunkHeight = 0;


			// Clear out the old canvases and remove them
			while (canvases.length)
			{
				canvases.pop().remove();
			}
			// And the assorted <br> tags as well
			canvas_container.children().each(function(){$(this).remove();});

			var devicePixelRatio = window.devicePixelRatio || 1;

			console.log('Pixel ratio', devicePixelRatio);

			for (var x = 0; x * maxDrawHeight < page_height; x += 1)
			{
				var newCanvas = $('<canvas/>');
				canvas_container.append(newCanvas);
				canvas_container.append($('<br/>'));
				canvases.push(newCanvas);

				var currentCanvas = newCanvas[0];

				// make sure the canvas is always at least full screen, even if the page is more narrow than the screen
				if (page_width > windowWidth())
				{
					currentCanvas.style.width = page_width + 'px';
					currentCanvas.width = page_width * devicePixelRatio;
					// currentCanvas.prop({width: page_width+'px'});
				}
				else
				{
					currentCanvas.style.width = windowWidth() + 'px';
					currentCanvas.width = windowWidth() * devicePixelRatio;
					// currentCanvas.prop({width: page_width+'px'});
				}


				// Draw canvas chunks
				if (runningHeight > maxDrawHeight)
				{
					// TODO: Clean up this mess at some point
					currentCanvas.style.height = maxDrawHeight + 'px';
					currentCanvas.height = maxDrawHeight * devicePixelRatio;
					chunkHeight    = maxDrawHeight;                 // Height of the current canvas chunk
					xOffset       += maxDrawHeight;                 // Current draw x-offset
					runningHeight -= maxDrawHeight;                 // Remaining image height to draw
				}
				else
				{
					currentCanvas.style.height = runningHeight + 'px';
					currentCanvas.height = runningHeight * devicePixelRatio;
					chunkHeight    = runningHeight;
					xOffset       += runningHeight;
					runningHeight -= runningHeight;
				}

				var context = currentCanvas.getContext('2d');

				var imXPos = offsetW;
				var imYPos = (chunkHeight - xOffset) * devicePixelRatio;
				var imXSz  = page_width  * devicePixelRatio;
				var imYSz  = page_height * devicePixelRatio;

				context.drawImage(image, imXPos, imYPos, imXSz, imYSz);
			}

		};


		/**
		 * Increment the counter and draw the page in the canvas
		 *
		 * @see #drawPage
		 */
		ComicBook.prototype.drawNextPage = function () {

			var page;

			try {
				page = self.getPage(pointer+1);
			} catch (e) {}

			if (!page) { return false; }

			if (pointer + 1 < pages.length) {
				pointer += 1;
				try {
					self.drawPage();
				} catch (e) {}
			}

			// make sure the top of the page is in view
			window.scroll(0, 0);
		};

		/**
		 * Decrement the counter and draw the page in the canvas
		 *
		 * @see #drawPage
		 */
		ComicBook.prototype.drawPrevPage = function () {

			var page;

			try {
				page = self.getPage(pointer-1);
			} catch (e) {}

			if (!page) { return false; }

			is_double_page_spread = (page.width > page.height); // need to run double page check again here as we are going backwards

			if (pointer > 0) {
				pointer -= 1;
				self.drawPage();
			}

			// make sure the top of the page is in view
			window.scroll(0, 0);
		};


		ComicBook.prototype.navigation = function (e) {

			// disable navigation when the overlay is showing
			if ($('#cb-loading-overlay').is(':visible')) { return false; }

			var side = false;

			switch (e.type)
			{

			case 'click':
				side = e.currentTarget.getAttribute('data-navigate-side');
				break;

			case 'keydown':

				// navigation
				if (e.keyCode === options.keyboard.previous)
				{
					side = 'left';
				}
				if (e.keyCode === options.keyboard.next)
				{
					side = 'right';
				}

				// display controls
				if (e.keyCode === options.keyboard.toolbar) {
					self.toggleUIOverlay();
				}
				if (e.keyCode === options.keyboard.toggleLayout) {
					self.toggleLayout();
				}

				// display thumbnail browser
				if (e.keyCode === options.keyboard.thumbnails) {
					self.toggleThumbnails();
				}
				break;

			default:
				throw ComicBookException.INVALID_NAVIGATION_EVENT + ' ' + e.type;
			}


			if (side)
			{



				e.preventDefault();
				e.stopPropagation();

				if (side === 'center')
				{
					console.log('Center clicked? Toggling toolbar');
					self.toggleUIOverlay();
				}
				else if (side === 'bottom')
				{
					// TODO: Add a nice pop-up label for the current zoom-mode.
					var curModeIndice = zoomModes.indexOf(options.zoomMode);
					curModeIndice = (curModeIndice + 1) % zoomModes.length;
					options.zoomMode = zoomModes[curModeIndice];
					console.log('Zoom Mode!', options.zoomMode);
					self.drawPage();
					$('#cb-status-left').show().delay(1000).fadeOut();
				}
				else
				{

					console.log('Page change event!');
					// western style (left to right)
					if (!options.manga) {
						if (side === 'left')
						{
							self.drawPrevPage();
						}
						if (side === 'right')
						{
							self.drawNextPage();
						}
					}
					// manga style (right to left)
					else {
						if (side === 'left') { self.drawNextPage(); }
						if (side === 'right') { self.drawPrevPage(); }
					}


					// Close any open toolbars
					self.hideToolBar();
				}

				self.updateInfoPanel();
				return false;
			}
		};

		ComicBook.prototype.toggleReadingMode = function () {
			options.manga = !options.manga;
			self.getControl('toolbar')
				.find('.manga-' + options.manga).show().end()
				.find('.manga-' + !options.manga).hide();
			self.drawPage();
		};

		ComicBook.prototype.toggleThumbnails = function () {
			// TODO: show page numbers
			// TODO: in double page mode merge both pages into a single link
			// TODO: only load thumbnails when they are in view
			// TODO: keyboard navigation (left / right / up / down / enter)
			// TODO: highlight currently selected thumbnail
			// TODO: focus on current page
			// TODO: toolbar button
			var $thumbnails = self.getControl('thumbnails');
			$thumbnails.html('');
			self.toggleControl('thumbnails');
			$.each(pages, function (i, img) {
				var $img = $(img).clone();
				var $link = $('<a>').attr('href', '#' + i).append($img);
				$link.on('click', function () {
					self.hideControl('thumbnails');
				});
				$thumbnails.append($link);
			});
		};

		ComicBook.prototype.toggleUIOverlay = function () {
			self.toggleControl('toolbar');
			var toolbar = self.getControl('toolbar');
			if(toolbar.is(':visible'))
			{
				$('#cb-status-right').show();
				$('#cb-status-left').show();
			}
			else

			{
				$('#cb-status-right').hide();
				$('#cb-status-left').hide();
			}

		};

		ComicBook.prototype.destroy = function () {

			$.each(this.controls, function (name, $control) {
				$control.remove();
			});

			$.each(canvases, function (name, $canvasItem) {

				$canvasItem.width = 0;
				$canvasItem.height = 0;

			});

			window.removeEventListener('keydown', this.navigation, false);


			// $(this).trigger('destroy');
		};

	}

	return ComicBook;

})(jQuery);

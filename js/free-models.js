(function(global){
  'use strict';
  const CATALOG_URL = './models/free-models.json';
  const FreeModels = {
    catalog: [],
    async load(){
      try {
        const response = await fetch(CATALOG_URL, {cache:'no-store'});
        if(!response.ok) throw new Error('catalogue HTTP '+response.status);
        const data = await response.json();
        this.catalog = Array.isArray(data.models) ? data.models : [];
        global.dispatchEvent(new CustomEvent('jarvis:models-loaded', {detail:data}));
        return data;
      } catch (error) {
        console.warn('[JARVIS] free model catalogue unavailable', error);
        return {models:[], unresolved:[]};
      }
    },
    openRouterIds(){ return this.catalog.filter(model => model.provider === 'OpenRouter').map(model => model.id); },
    find(id){ return this.catalog.find(model => model.id === id); }
  };
  global.JARVIS_FreeModels = FreeModels;
})(window);

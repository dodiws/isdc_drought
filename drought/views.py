from django.shortcuts import render
# from .models import (
#     AfgFldzonea100KRiskLandcoverPop,
#     FloodRiskExposure,
#     Glofasintegrated,
#     )
from geodb.models import (
    AfgAdmbndaAdm1,
    AfgAdmbndaAdm2,
    AfgAirdrmp,
    # AfgAvsa,
    AfgCapaGsmcvr,
    AfgCaptAdm1ItsProvcImmap,
    AfgCaptAdm1NearestProvcImmap,
    AfgCaptAdm2NearestDistrictcImmap,
    AfgCaptAirdrmImmap,
    AfgCaptHltfacTier1Immap,
    AfgCaptHltfacTier2Immap,
    AfgCaptHltfacTier3Immap,
    AfgCaptHltfacTierallImmap,
    AfgHltfac,
    # AfgIncidentOasis,
    AfgLndcrva,
    AfgPplp,
    AfgRdsl,
    districtsummary,
    # earthquake_events,
    # earthquake_shakemap,
    forecastedLastUpdate,
    LandcoverDescription,
    provincesummary,
    tempCurrentSC,
    # villagesummaryEQ,
    )
from geodb.geo_calc import (
    getCommonUse,
    # getFloodForecastBySource,
    # getFloodForecastMatrix,
    getGeoJson,
    getProvinceSummary_glofas,
    getProvinceSummary,
    getRawBaseLine,
    # getRawFloodRisk,
    # getSettlementAtFloodRisk,
    getShortCutData,
    getTotalArea,
    getTotalBuildings,
    getTotalPop,
    getTotalSettlement,
    getRiskNumber,
    )
from geodb.views import (
    get_nc_file_from_ftp,
    getCommonVillageData,
    )
# from geodb.geoapi import getRiskExecuteExternal
# from .riverflood import getFloodForecastBySource
from django.db import connection, connections
from django.db.models import Count, Sum
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW
from geonode.utils import include_section, none_to_zero, query_to_dicts, RawSQL_nogroupby, ComboChart, dict_ext
from matrix.models import matrix
from pprint import pprint
from pytz import timezone, all_timezones
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource, Resource
from urlparse import urlparse
from django.conf import settings
from netCDF4 import Dataset, num2date
from django.utils.translation import ugettext as _
from graphos.renderers import flot, gchart
from graphos.sources.simple import SimpleDataSource
from django.shortcuts import render_to_response
from django.template import RequestContext

import json
import time, datetime
import timeago
import pandas as pd

def get_dashboard_meta(page_name):
    if page_name == 'drought':
        return {'function':dashboard_drought, 'template':'dash_drought.html'}
    return None

# from geodb.geo_calc

def getDroughtRisk(request, filterLock, flag, code, woy=None, includes=[], excludes=[], **kwargs):
    
    if not woy:
        year, month, day = kwargs.get('date', str(datetime.date.today())).split('-')
        woy = year + '%03d' % datetime.date(int(year), int(month), int(day)).isocalendar()[1]
        woy = getClosestDroughtWOY(woy)
        
    targetBase = AfgLndcrva.objects.all()
    response = getCommonUse(request, flag, code)

    if flag not in ['entireAfg','currentProvince']:
        response['Population']=getTotalPop(filterLock, flag, code, targetBase)
        response['Area']=getTotalArea(filterLock, flag, code, targetBase)
        response['Buildings']=getTotalBuildings(filterLock, flag, code, targetBase)
        response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)
    else :
        tempData  = getShortCutData(flag,code)
        response['Population']= tempData['Population']
        response['Area']= tempData['Area']
        response['Buildings']= tempData['total_buildings']
        response['settlement']= tempData['settlements']

    sql_tpl = '''
        SELECT
            afg_lndcrva.agg_simplified_description,
            {adm_code},
            {adm_name},
            history_drought.min,
            COALESCE(ROUND(SUM(afg_lndcrva.area_population)), 0) AS pop,
            COALESCE(ROUND(SUM(afg_lndcrva.area_buildings)), 0) AS building,
            COALESCE(ROUND((SUM(afg_lndcrva.area_sqm) / 1000000)::NUMERIC, 1), 0) AS area
        FROM afg_lndcrva
        INNER JOIN history_drought
        ON history_drought.ogc_fid = afg_lndcrva.ogc_fid
        WHERE afg_lndcrva.aggcode_simplified NOT IN ('WAT', 'BRS', 'BSD', 'SNW')
        AND aggcode NOT IN ('AGR/NHS', 'NHS/NFS', 'NHS/BRS', 'NHS/WAT', 'NHS/URB', 'URB/AGT', 'URB/AGI', 'URB/NHS', 'URB/BRS', 'URB/BSD')
        AND history_drought.woy = '{woy}'
        {extra_condition}
        GROUP BY 
            afg_lndcrva.agg_simplified_description, 
            {adm_code},
            {adm_name},
            history_drought.min
        ORDER BY 
            afg_lndcrva.agg_simplified_description, 
            {adm_code}, 
            {adm_name},
            history_drought.min        
        '''

    sql_total_tpl = '''
        SELECT
            afg_lndcrva.agg_simplified_description,
            {adm_code},
            {adm_name},
            COALESCE(ROUND(SUM(afg_lndcrva.area_population)), 0) AS pop,
            COALESCE(ROUND(SUM(afg_lndcrva.area_buildings)), 0) AS building,
            COALESCE(ROUND((SUM(afg_lndcrva.area_sqm) / 1000000)::NUMERIC, 1), 0) AS area
        FROM afg_lndcrva
        WHERE afg_lndcrva.aggcode_simplified NOT IN ('WAT', 'BRS', 'BSD', 'SNW')
        AND aggcode NOT IN ('AGR/NHS', 'NHS/NFS', 'NHS/BRS', 'NHS/WAT', 'NHS/URB', 'URB/AGT', 'URB/AGI', 'URB/NHS', 'URB/BRS', 'URB/BSD')
        {extra_condition}
        GROUP BY 
            afg_lndcrva.agg_simplified_description, 
            {adm_code},
            {adm_name}
        ORDER BY 
            afg_lndcrva.agg_simplified_description, 
            {adm_code}, 
            {adm_name}
        '''

    sql_extra_condition_tpl = "AND {parent_adm_col} = '{parent_adm_val}'"
    sql_param = {'woy':woy, 'extra_condition':''}

    if flag=='entireAfg':
        sql_param.update({'adm_code': 'prov_code', 'adm_name': 'prov_na_en'})
    elif flag=='currentProvince':
        sql_param.update({'adm_code': 'dist_code', 'adm_name': 'dist_na_en', 'parent_adm_val':code})
        if len(str(code)) > 2:
            sql_param.update({'parent_adm_col':'dist_code'})
        else:
            sql_param.update({'parent_adm_col':'prov_code'})
        sql_param['extra_condition'] = sql_extra_condition_tpl.format(**sql_param)
    elif flag=='drawArea':
        sql_param['extra_condition'] = 'AND ST_Intersects(wkb_geometry, %s)' % filterLock

    sql = sql_tpl.format(**sql_param)
    sql_total = sql_total_tpl.format(**sql_param)
    # print sql

    with connections['geodb'].cursor() as cursor:

        row = query_to_dicts(cursor, sql)
        counts = []
        for i in row:
            counts.append(i)

        row_total = query_to_dicts(cursor, sql_total)
        counts_total = []
        for i in row_total:
            counts_total.append(i)

    # enumeration
    droughtrisks = {
        0:_('Abnormally Dry Condition'), 
        1:_('Moderate'), 
        2:_('Severe'), 
        3:_('Extreme'), 
        4:_('Exceptional')
        }

    d = {}
    groupby_risk = {}
    groupby_lc_risk = {}
    groupby_adm_risk = {'adm_child':{}}

    if counts and counts_total:
        df = pd.DataFrame(counts, columns=counts[0].keys())
        df_total = pd.DataFrame(counts_total, columns=counts_total[0].keys())
        
        # calculate pop, building, area group by landcover, area, risk 
        for lc in df['agg_simplified_description'].unique():
            d[lc] = {'adm_child':{}}
            df_lc = df[df['agg_simplified_description']==lc]
            d[lc]['adm_parent'] = {
                'code' : code,
                'label': response['parent_label'],
                'risk_child' : {}
                }
            for risk in df_lc['min'].unique():
                risk_int = int(risk)
                df_risk = df_lc[df_lc['min']==risk]
                df_risk_agg = df_risk.agg({'pop':'sum','building':'sum','area':'sum'})
                d[lc]['adm_parent']['risk_child'][risk_int] =  {
                    'label': droughtrisks[risk_int],
                    'child': {
                        'pop':df_risk_agg['pop'],
                        'building':df_risk_agg['building'],
                        'area':df_risk_agg['area']
                        }
                    }
            for adm in df_lc[sql_param['adm_code']].unique():
                df_adm = df_lc[df_lc[sql_param['adm_code']]==adm]
                d[lc]['adm_child'][adm] = {
                    'code' : adm,
                    'label':df_adm.iloc[0][sql_param['adm_name']], 
                    'risk_child':{}
                    }
                for risk in df_adm['min'].unique():
                    risk_int = int(risk)
                    df_risk = df_adm[df_adm['min']==risk]
                    d[lc]['adm_child'][adm]['risk_child'][risk_int] =  {
                        'label': droughtrisks[risk_int],
                        'child': {
                            'pop':df_risk.iloc[0]['pop'],
                            'building':df_risk.iloc[0]['building'],
                            'area':df_risk.iloc[0]['area']
                            }
                        }

        # calculate pop, building, area group by risk
        df_risk = df.groupby(['min'], as_index=False).agg({'pop':'sum','building':'sum','area':'sum'})
        for idx in df_risk.index:
            risk_int = int(df_risk['min'][idx])
            groupby_risk[risk_int] = {
                'label': droughtrisks[risk_int],
                'child': {
                    'pop':df_risk['pop'][idx],
                    'building':df_risk['building'][idx],
                    'area':df_risk['area'][idx]
                    }
                }

        # calculate pop, area group by landcover, risk
        for lc, lc_group in df.groupby(['agg_simplified_description']):
            groupby_lc_risk[lc] = {'risk_child':{}}
            agg = df_total[df_total['agg_simplified_description']==lc].agg({'pop':'sum','building':'sum','area':'sum'})
            groupby_lc_risk[lc]['total_child'] = {
                'pop': agg['pop'],
                'building': agg['building'],
                'area': agg['area']
            }        
            agg_risk = lc_group[lc_group['agg_simplified_description']==lc].agg({'pop':'sum','building':'sum','area':'sum'})
            groupby_lc_risk[lc]['total_risk_child'] = {
                'pop': agg_risk['pop'],
                'building': agg_risk['building'],
                'area': agg_risk['area']
            }        
            for risk, risk_group in lc_group.groupby(['min']):
                agg = risk_group.agg({'pop':'sum','building':'sum','area':'sum'})
                risk_int = int(risk)
                groupby_lc_risk[lc]['risk_child'][risk_int] = {
                    'label': droughtrisks[risk_int],
                    'child': {
                        'pop': agg['pop'],
                        'building': agg['building'],
                        'area': agg['area']
                    }
                }        

        # calculate pop, building, area group by adm, risk
        for adm, adm_group in df.groupby([sql_param['adm_code'], sql_param['adm_name']]):
            adm_code, adm_name = adm
            groupby_adm_risk['adm_child'][adm_code] = {
                'adm_code': adm_code,
                'adm_name': adm_name,
                'risk_child': {}
            }
            for risk, risk_group in adm_group.groupby(['min']):
                agg = risk_group.agg({'pop':'sum','building':'sum','area':'sum'})
                risk_int = int(risk)
                groupby_adm_risk['adm_child'][adm_code]['risk_child'][risk_int] = {
                    'label': droughtrisks[risk_int],
                    'child': {
                        'pop': agg['pop'],
                        'building': agg['building'],
                        'area': agg['area']
                    }
                }        
    
    # geojson
    if include_section('GeoJson', includes, excludes):
        response['GeoJson'] = json.dumps(getGeoJson(request, flag, code))

    woy_datestart, woy_dateend = getYearRangeFromWeek(woy) if woy else None, None

    response.update({
        # 'queryresult':counts,
        'woy': woy,
        'woy_datestart': woy_datestart,
        'woy_dateend': woy_dateend,
        'drought_data':{
            'group_by':{
                'adm_risk': groupby_adm_risk,
                'landcover_area_risk': {'lc_child':d},
                'landcover_risk': groupby_lc_risk,
                'risk': groupby_risk
                },
            }
        })

    return response

# from geodb.geoapi
 
def getDroughtStatistics(filterLock, flag, code, woy, includes=[], excludes=[]):
    import pandas as pd

    if flag=='entireAfg':
        sql = "select \
            afg_lndcrva.agg_simplified_description, history_drought.min, \
            COALESCE(ROUND(sum(afg_lndcrva.area_population)),0) as pop, \
            COALESCE(ROUND(sum(afg_lndcrva.area_buildings)),0) as building, \
            COALESCE(ROUND((sum(afg_lndcrva.area_sqm)/1000000)::NUMERIC,1),0) as area \
            from afg_lndcrva inner join history_drought on history_drought.ogc_fid=afg_lndcrva.ogc_fid \
            where afg_lndcrva.aggcode_simplified not in ('WAT','BRS', 'BSD', 'SNW') and aggcode not in ('AGR/NHS','NHS/NFS','NHS/BRS','NHS/WAT','NHS/URB','URB/AGT','URB/AGI','URB/NHS','URB/BRS','URB/BSD') \
            and history_drought.woy='"+str(woy)+"'\
            group by afg_lndcrva.agg_simplified_description, history_drought.min \
            order by afg_lndcrva.agg_simplified_description, history_drought.min"
    elif flag =='currentProvince':
        if len(str(code)) > 2:
            ff0001 =  "afg_lndcrva.dist_code  = '"+str(code)+"'"
        else :
            ff0001 =  "afg_lndcrva.prov_code  = '"+str(code)+"'" 
        sql = "select \
            afg_lndcrva.agg_simplified_description, history_drought.min, \
            COALESCE(ROUND(sum(afg_lndcrva.area_population)),0) as pop, \
            COALESCE(ROUND(sum(afg_lndcrva.area_buildings)),0) as building, \
            COALESCE(ROUND((sum(afg_lndcrva.area_sqm)/1000000)::NUMERIC,1),0) as area \
            from afg_lndcrva inner join history_drought on history_drought.ogc_fid=afg_lndcrva.ogc_fid \
            where afg_lndcrva.aggcode_simplified not in ('WAT','BRS', 'BSD', 'SNW') and aggcode not in ('AGR/NHS','NHS/NFS','NHS/BRS','NHS/WAT','NHS/URB','URB/AGT','URB/AGI','URB/NHS','URB/BRS','URB/BSD') \
            and history_drought.woy='"+str(woy)+"'\
            and "+ff0001+" \
            group by afg_lndcrva.agg_simplified_description, history_drought.min \
            order by afg_lndcrva.agg_simplified_description, history_drought.min"
    elif flag =='drawArea':
        sql = "select \
            afg_lndcrva.agg_simplified_description, history_drought.min, \
            COALESCE(ROUND(sum(afg_lndcrva.area_population)),0) as pop, \
            COALESCE(ROUND(sum(afg_lndcrva.area_buildings)),0) as building, \
            COALESCE(ROUND((sum(afg_lndcrva.area_sqm)/1000000)::NUMERIC,1),0) as area \
            from afg_lndcrva inner join history_drought on history_drought.ogc_fid=afg_lndcrva.ogc_fid \
            where afg_lndcrva.aggcode_simplified not in ('WAT','BRS', 'BSD', 'SNW') and aggcode not in ('AGR/NHS','NHS/NFS','NHS/BRS','NHS/WAT','NHS/URB','URB/AGT','URB/AGI','URB/NHS','URB/BRS','URB/BSD') \
            and history_drought.woy='"+str(woy)+"' \
            and ST_Intersects(afg_lndcrva.wkb_geometry,"+filterLock+") \
            group by afg_lndcrva.agg_simplified_description, history_drought.min \
            order by afg_lndcrva.agg_simplified_description, history_drought.min"
    else:   
        sql = "select \
            afg_lndcrva.agg_simplified_description, history_drought.min, \
            COALESCE(ROUND(sum(afg_lndcrva.area_population)),0) as pop, \
            COALESCE(ROUND(sum(afg_lndcrva.area_buildings)),0) as building, \
            COALESCE(ROUND((sum(afg_lndcrva.area_sqm)/1000000)::NUMERIC,1),0) as area \
            from afg_lndcrva inner join history_drought on history_drought.ogc_fid=afg_lndcrva.ogc_fid \
            where afg_lndcrva.aggcode_simplified not in ('WAT','BRS', 'BSD', 'SNW') and aggcode not in ('AGR/NHS','NHS/NFS','NHS/BRS','NHS/WAT','NHS/URB','URB/AGT','URB/AGI','URB/NHS','URB/BRS','URB/BSD') \
            and history_drought.woy='"+str(woy)+"'\
            and ST_Intersects(afg_lndcrva.wkb_geometry,"+filterLock+") \
            group by afg_lndcrva.agg_simplified_description, history_drought.min \
            order by afg_lndcrva.agg_simplified_description, history_drought.min" 
   
    cursor = connections['geodb'].cursor()
    row = query_to_dicts(cursor, sql)
    counts = []
    for i in row:
        counts.append(i)
    cursor.close()

    d = {}
    if counts:
        df = pd.DataFrame(counts, columns=counts[0].keys())

        for i in df['agg_simplified_description'].unique():
            d[i] = [{int(df['min'][j]): {
                        'pop':df['pop'][j],
                        'building':df['building'][j],
                        'area':df['area'][j]
                    } 
            } for j in df[df['agg_simplified_description']==i].index]

    selected_date_range = getYearRangeFromWeek(woy) if woy else [None, None]

    data = {'record':[], 'woy':woy, 'start':selected_date_range[0], 'end':selected_date_range[1]}
    for i in d:
        detail = []
        for det in d[i]:
            ket = None
            if det.keys()[0] == 0:
                ket = 'Abnormally Dry Condition'
            elif det.keys()[0] == 1:   
                ket = 'Moderate'
            elif det.keys()[0] == 2:   
                ket = 'Severe'
            elif det.keys()[0] == 3:   
                ket = 'Extreme'
            elif det.keys()[0] == 4:   
                ket = 'Exceptional' 

            val = {}
            val.update({'name':ket})
            val.update(det[det.keys()[0]])
            detail.append(val)

        data['record'].append(
            {
                'name':i,
                'detail': detail,
                'woy':woy
            }
        )
        
    return data

def getClosestDroughtWOY(woy):
    sql = "select distinct woy from history_drought \
            where to_timestamp(concat(substring(woy,6,2),' ',substring(woy,1,4)), 'W YYYY')::date < to_timestamp(concat(substring('"+woy+"',6,2),' ',substring('"+woy+"',1,4)), 'W YYYY')::date \
            ORDER BY woy DESC \
            LIMIT 1"
    cursor = connections['geodb'].cursor()
    row = query_to_dicts(cursor, sql)  
    data = None 
    for i in row:
        data = i['woy']
    cursor.close()    
    return data

class getDrought(ModelResource):

    class Meta:
        resource_name = 'getdrought'
        allowed_methods = ['post']
        detail_allowed_methods = ['post']
        cache = SimpleCache() 
        object_class=None

    def post_list(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        response = self.getData(request)
        return self.create_response(request, response)   

    def getData(self, request):
        boundaryFilter = json.loads(request.body)

        temp1 = []
        for i in boundaryFilter['spatialfilter']:
            temp1.append('ST_GeomFromText(\''+i+'\',4326)')

        temp2 = 'ARRAY['
        first=True
        for i in temp1:
            if first:
                 temp2 = temp2 + i
                 first=False
            else :
                 temp2 = temp2 + ', ' + i  

        temp2 = temp2+']'
        
        filterLock = 'ST_Union('+temp2+')'
        flag = boundaryFilter['flag']
        code = boundaryFilter['code']
        dateIn = boundaryFilter['date'].split('-')

        closest_woy = getClosestDroughtWOY(dateIn[0] + '%03d' % datetime.date(int(dateIn[0]), int(dateIn[1]), int(dateIn[2])).isocalendar()[1])

        response = {}
        response = getDroughtStatistics(filterLock,flag,code, closest_woy)
        return response

def getYearRangeFromWeek(woy):
    year = int(woy[:-3])
    week = int(woy[4:])
    d = datetime.date(year,1,1)
    d = d - datetime.timedelta(d.weekday())
    dlt = datetime.timedelta(days = (week-1)*7)
    return str(d + dlt),  str(d + dlt + datetime.timedelta(days=6))

class getClosestDroughtWOYLayerAPI(ModelResource):
    class Meta:
        resource_name = 'getdroughtlayer'
        allowed_methods = ['post']
        detail_allowed_methods = ['post']
        cache = SimpleCache() 
        object_class=None

    def post_list(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        response = self.getData(request)
        return self.create_response(request, response)   

    def getData(self, request):
        boundaryFilter = json.loads(request.body)
        dateIn = boundaryFilter['date'].split('-')
        closest_woy = getClosestDroughtWOY(dateIn[0] + '%03d' % datetime.date(int(dateIn[0]), int(dateIn[1]), int(dateIn[2])).isocalendar()[1])

        response = {'woy':closest_woy}
        return response

def dashboard_drought(request, filterLock, flag, code, includes=[], excludes=[]):
	response = dict_ext(getCommonUse(request, flag, code))
	response['source'] = getDroughtRisk(request, filterLock, flag, code)

	return response

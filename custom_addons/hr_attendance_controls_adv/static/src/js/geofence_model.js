/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Model } from "@web/model/model";
import { KeepLast } from "@web/core/utils/concurrency";

export class GeofenceModel extends Model {
    setup(params) {
        this.metaData = {
            ...params,
        };
        this.data = {
            count: 0,
            records: [],
        };
        this.keepLast = new KeepLast();
    }
    async load(params) {
        const metaData = {
            ...this.metaData,
            ...params,
        };
        this.data = await this._fetchData(metaData);
        this.metaData = metaData;
    }
    async _fetchData(metaData) {
        var self = this; 
        const data = {
            records: [],
        }
        const results = await this.keepLast.add(this._fetchRecordData(metaData));
        if (results && results[0].records){
            data.records = results[0].records;
        }else{
            data.records = [];
        }
        return data;
    }
    _getFields(metaData) {
        const fields = new Set([]);
        if (metaData.fieldNames) {
            fields.add(metaData.fieldNames);
        }
        return [...fields];
    }
    async _fetchRecordData(metaData){
        const promises = [];
        const fields = this._getFields(metaData);
        const specification = {};
        for (const fieldName of fields) {
            specification[fieldName] = {};
            if (metaData.fields[fieldName].type === "many2one") {
                specification[fieldName].fields = { display_name: {} };
            }
        }
        const orderBy = [];
        if (metaData.defaultOrder) {
            orderBy.push(metaData.defaultOrder);
            if (metaData.defaultOrder) {
                orderBy.push("asc");
            }

        }
        var result = await this.orm.webSearchRead(metaData.resModel, metaData.domain, {
            specification: specification,
            limit: metaData.limit,
            offset: metaData.offset,
            order: orderBy.join(" "),
            context: metaData.context,
        });
        promises.push(result);
        return Promise.all(promises);
    }
}

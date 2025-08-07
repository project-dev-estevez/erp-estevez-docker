/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Service to handle recruitment stages
 * Avoids repeating stage queries in multiple places
 */
class RecruitmentStageService {
    constructor(env, { orm }) {
        this.orm = orm;
        this._firstContactCache = null;
        this._firstInterviewCache = null;  // ✅ Cache for First Interview
    }

    /**
     * Gets the "First Contact" stage
     * Only queries once, then uses cache
     */
    async getFirstContactStage() {
        if (this._firstContactCache) {
            return this._firstContactCache;
        }

        try {
            const stages = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (stages.length > 0) {
                this._firstContactCache = stages[0];
                return this._firstContactCache;
            } else {
                return null;
            }
        } catch (error) {
            return null;
        }
    }

    /**
     * Gets the "First Interview" stage
     * Only queries once, then uses cache
     */
    async getFirstInterviewStage() {
        if (this._firstInterviewCache) {
            return this._firstInterviewCache;
        }

        try {
            const stages = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primera entrevista']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (stages.length > 0) {
                this._firstInterviewCache = stages[0];
                return this._firstInterviewCache;
            } else {
                return null;
            }
        } catch (error) {
            return null;
        }
    }

    /**
     * Creates domain for candidates post-First Interview
     * @param {Array} baseDomain - Base domain conditions
     * @param {Boolean} includeAllStatuses - Include all statuses (ongoing, hired, refused, inactive)
     * @returns {Array} Domain with First Interview conditions
     */
    async getPostFirstInterviewDomain(baseDomain = [], includeAllStatuses = true) {
        const firstInterview = await this.getFirstInterviewStage();
        if (!firstInterview) {
            console.warn("⚠️ RecruitmentStageService: 'First Interview' stage not found");
            return baseDomain;
        }

        const domain = [
            ...baseDomain,
            ['stage_id.sequence', '>=', firstInterview.sequence]
        ];

        // ✅ Include ALL statuses (ongoing, hired, refused, inactive)
        if (includeAllStatuses) {
            domain.push(
                "|", "|", "|",
                ["application_status", "=", "ongoing"],
                ["application_status", "=", "hired"],
                ["application_status", "=", "refused"],
                ["active", "=", false]
            );
        }

        return domain;
    }

    /**
     * Gets all stages from first contact (inclusive)
     */
    async getStagesFromFirstContact() {
        const firstContact = await this.getFirstContactStage();
        if (!firstContact) {
            return [];
        }

        try {
            const stages = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['sequence', '>=', firstContact.sequence]],
                ['id', 'name', 'sequence'],
                { order: 'sequence asc' }
            );
            return stages;
        } catch (error) {
            return [];
        }
    }

    /**
     * Creates domain for rejected candidates from first contact
     */
    async getRejectedDomainFromFirstContact(baseDomain = []) {
        const firstContact = await this.getFirstContactStage();
        if (!firstContact) {
            return [...baseDomain, ['application_status', '=', 'refused']];
        }

        return [
            ...baseDomain,
            ['stage_id.sequence', '>=', firstContact.sequence],
            ['application_status', '=', 'refused']
        ];
    }

    /**
     * Clears all caches (useful for tests or when stages are modified)
     */
    clearCache() {
        this._firstContactCache = null;
        this._firstInterviewCache = null;
    }
}

// Register the service in Odoo
registry.category("services").add("recruitment_stage", {
    dependencies: ["orm"],
    start(env, { orm }) {
        return new RecruitmentStageService(env, { orm });
    },
});

export { RecruitmentStageService };
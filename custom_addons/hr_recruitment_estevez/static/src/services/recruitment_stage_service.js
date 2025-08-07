/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Service to handle recruitment stages
 * Avoids repeating "First Contact" queries in multiple places
 */
class RecruitmentStageService {
    constructor(env, { orm }) {
        this.orm = orm;
        this._firstContactCache = null; // Cache to avoid repeated queries
    }

    /**
     * Gets the "First Contact" stage
     * Only queries once, then uses cache
     */
    async getFirstContactStage() {
        // If we already have the info in cache, return it
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
            // If we don't find first contact, only filter by rejected
            return [...baseDomain, ['application_status', '=', 'refused']];
        }

        return [
            ...baseDomain,
            ['stage_id.sequence', '>=', firstContact.sequence],
            ['application_status', '=', 'refused']
        ];
    }

    /**
     * Clears the cache (useful for tests or when stages are modified)
     */
    clearCache() {
        this._firstContactCache = null;
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
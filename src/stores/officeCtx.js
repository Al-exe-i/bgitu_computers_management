import { defineStore } from 'pinia'

export const useAudienceContext = defineStore('audienceContext', {
    state: () => ({
        officeId: null,
        fromOffice: false
    }),

    actions: {
        setOffice(officeId) {
            this.officeId = officeId
            this.fromOffice = true
        },
        clear() {
            this.officeId = null
            this.fromOffice = false
        }
    },

})
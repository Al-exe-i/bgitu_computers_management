import { defineStore } from 'pinia';
import api from '@/services/api';

export const useOfficeStore = defineStore('offices', {
    state: () => ({
        list: [],
        loading: false
    }),

    actions: {
        async fetchOffices()
        {
            this.loading = true;
            try
            {
                const res = await api.get('/offices/all_short');
                this.list = res.data;
            } catch (e) {
                console.error('Ошибка загрузки корпусов', e);
            } finally {
                this.loading = false;
            }
        },

        // Добавление (чтобы не перезагружать весь список)
        addOffice(office)
        {
            this.list.push(office);
        },

        // Удаление
        removeOffice(id)
        {
            this.list = this.list.filter(o => o.id !== id);
        },

        // Обновление
        updateOffice(updatedOffice)
        {
            const index = this.list.findIndex(o => o.id === updatedOffice.id);
            if (index !== -1) {
                this.list[index] = updatedOffice;
            }
        }
    }
});

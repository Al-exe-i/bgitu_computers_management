import { shallowRef, readonly } from 'vue';

const activeRequest = shallowRef(null);
export const confirmationRequest = readonly(activeRequest);
let pending = null;
let nextId = 0;

export function answerConfirmation(id, accepted = false) {
  if (!pending || pending.id !== id) return;
  const resolve = pending.resolve;
  pending = null;
  activeRequest.value = null;
  resolve(accepted === true);
}

// Подтверждение принадлежит странице: уход со страницы отменяет ожидающее действие.
export function createConfirmationScope() {
  let disposed = false;
  let ownedId = null;
  return {
    ask(options) {
      if (disposed || pending) return Promise.resolve(false);
      const id = ++nextId;
      ownedId = id;
      return new Promise(resolve => {
        pending = { id, resolve };
        activeRequest.value = {
          title: 'Подтвердить действие?', message: '', subject: '', detail: '',
          confirmLabel: 'Подтвердить', cancelLabel: 'Отмена', tone: 'warning',
          ...options, id,
        };
      }).then(accepted => !disposed && accepted);
    },
    cancel() {
      disposed = true;
      answerConfirmation(ownedId, false);
    },
  };
}

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';

// PrimeVue
import PrimeVue from 'primevue/config';
import 'primevue/resources/themes/lara-light-blue/theme.css';
import 'primevue/resources/primevue.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

// PrimeVue Components
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import FileUpload from 'primevue/fileupload';
import ProgressBar from 'primevue/progressbar';
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Toast from 'primevue/toast';
import ToastService from 'primevue/toastservice';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Divider from 'primevue/divider';
import Tag from 'primevue/tag';
import Chip from 'primevue/chip';
import ConfirmDialog from 'primevue/confirmdialog';
import ConfirmationService from 'primevue/confirmationservice';

const app = createApp(App);

// Utilisation de PrimeVue
app.use(PrimeVue);
app.use(ToastService);
app.use(ConfirmationService);
app.use(router);
app.use(store);

// Enregistrement des composants PrimeVue
app.component('Button', Button);
app.component('InputText', InputText);
app.component('Dropdown', Dropdown);
app.component('FileUpload', FileUpload);
app.component('ProgressBar', ProgressBar);
app.component('Card', Card);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Dialog', Dialog);
app.component('Toast', Toast);
app.component('TabView', TabView);
app.component('TabPanel', TabPanel);
app.component('Divider', Divider);
app.component('Tag', Tag);
app.component('Chip', Chip);
app.component('ConfirmDialog', ConfirmDialog);

app.mount('#app');

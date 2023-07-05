export interface ConfigMessage {
    severity: 'info' | 'warning' | 'error';
    message: string;
}
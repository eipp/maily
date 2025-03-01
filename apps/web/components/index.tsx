import { lazy, type ComponentType } from 'react';
import { LoadingPulse } from './LoadingPulse';

interface EmailEditorProps {}
interface ImageUploaderProps {}
interface TemplateSelectorProps {}
interface DashboardProps {}
interface FileManagerProps {}
interface CampaignManagerProps {}
interface CampaignEditorProps {}
interface DataVisualizationProps {}
interface ImageEditorProps {}
interface AuthFormsProps {}
interface SettingsPanelProps {}
interface GalleryProps {}
interface RichTextEditorProps {}

export const EmailEditor = lazy<ComponentType<EmailEditorProps>>(() => import('./EmailEditor'));
export const ImageUploader = lazy<ComponentType<ImageUploaderProps>>(() => import('./ImageUploader'));
export const TemplateSelector = lazy<ComponentType<TemplateSelectorProps>>(() => import('./TemplateSelector'));
export const Dashboard = lazy<ComponentType<DashboardProps>>(() => import('./Dashboard'));
export const FileManager = lazy<ComponentType<FileManagerProps>>(() => import('./FileManager'));
export const CampaignManager = lazy<ComponentType<CampaignManagerProps>>(() => import('./CampaignManager'));
export const CampaignEditor = lazy<ComponentType<CampaignEditorProps>>(() => import('./CampaignEditor'));
export const DataVisualization = lazy<ComponentType<DataVisualizationProps>>(() => import('./DataVisualization'));
export const ImageEditor = lazy<ComponentType<ImageEditorProps>>(() => import('./ImageEditor'));
export const AuthForms = lazy<ComponentType<AuthFormsProps>>(() => import('./AuthForms'));
export const SettingsPanel = lazy<ComponentType<SettingsPanelProps>>(() => import('./SettingsPanel'));
export const Gallery = lazy<ComponentType<GalleryProps>>(() => import('./Gallery'));
export const RichTextEditor = lazy<ComponentType<RichTextEditorProps>>(() => import('./RichTextEditor'));

export { LoadingPulse };

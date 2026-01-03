{{- define "social_service.name" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- $name | lower | replace "_" "-" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "social_service.fullname" -}}
{{- $name := include "social_service.name" . -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | lower | replace "_" "-" | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | lower | replace "_" "-" | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "social_service.labels" -}}
app.kubernetes.io/name: {{ include "social_service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "social_service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "social_service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}


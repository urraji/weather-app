{{- define "weather.name" -}}
weather
{{- end -}}

{{- define "weather.fullname" -}}
{{ include "weather.name" . }}
{{- end -}}

{{- define "weather.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "weather.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

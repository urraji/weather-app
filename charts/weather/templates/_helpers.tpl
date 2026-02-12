{{- define "weather.name" -}}
weather
{{- end -}}

{{- define "weather.fullname" -}}
{{ .Release.Name }}-weather
{{- end -}}

import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
parsed = [
    {
        "status": "firing",
        "labels": {
            "alertgroup": "kubernetes-apps",
            "alertname": "KubeDaemonSetMisScheduled",
            "container": "kube-state-metrics",
            "daemonset": "svclb-traefik-cfbcf9b2",
            "endpoint": "http",
            "instance": "10.42.2.49:8080",
            "job": "kube-state-metrics",
            "namespace": "kube-system",
            "pod": "victoria-metrics-kube-state-metrics-865d4cc775-rj5r5",
            "prometheus": "monitoring/victoria-metrics-k8s",
            "service": "victoria-metrics-kube-state-metrics",
            "severity": "warning",
        },
        "annotations": {
            "description": "1 Pods of DaemonSet kube-system/svclb-traefik-cfbcf9b2 are running where they are not supposed to run on cluster .",
            "runbook_url": "https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubedaemonsetmisscheduled",
            "summary": "DaemonSet pods are misscheduled.",
        },
        "startsAt": "2026-05-27T23:07:00Z",
        "endsAt": "0001-01-01T00:00:00Z",
    },
    {
        "status": "resolved",
        "labels": {
            "alertgroup": "kubernetes-apps",
            "alertname": "KubeDaemonSetMisScheduled",
            "container": "kube-state-metrics",
            "daemonset": "svclb-traefik-cfbcf9b2",
            "endpoint": "http",
            "instance": "10.42.2.49:8080",
            "job": "kube-state-metrics",
            "namespace": "kube-system",
            "pod": "victoria-metrics-kube-state-metrics-865d4cc775-rj5r5",
            "prometheus": "monitoring/victoria-metrics-k8s",
            "service": "victoria-metrics-kube-state-metrics",
            "severity": "warning",
        },
        "annotations": {
            "description": "1 Pods of DaemonSet kube-system/svclb-traefik-cfbcf9b2 are running where they are not supposed to run on cluster .",
            "runbook_url": "https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubedaemonsetmisscheduled",
            "summary": "DaemonSet pods are misscheduled.",
        },
        "startsAt": "2026-05-27T23:07:00Z",
        "endsAt": "0001-01-01T00:00:00Z",
    },
]

not_parsed = [
    {
        "version": "4",
        "groupKey": "test",
        "truncatedAlerts": 2,
        "status": "resolved",
        "receiver": "tg-api",
        "groupLabels": "test",
        "commonLabels": 2,
        "commonAnnotations": 2,
        "externalURL": "dsf",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertgroup": "kubernetes-apps",
                    "alertname": "KubeDaemonSetMisScheduled123",
                    "container": "kube-state-metrics",
                    "daemonset": "svclb-traefik-cfbcf9b2",
                    "endpoint": "http",
                    "instance": "10.42.2.49:8080",
                    "job": "kube-state-metrics",
                    "tgChatId": "-10000000000",
                    "namespace": "kube-system",
                    "pod": "victoria-metrics-kube-state-metrics-865d4cc775-rj5r5",
                    "prometheus": "monitoring/victoria-metrics-k8s",
                    "service": "victoria-metrics-kube-state-metrics",
                    "severity": "warning",
                },
                "annotations": {
                    "description": "1 Pods of DaemonSet kube-system/svclba-traefik-cfbcf9b2 are running where they are not supposed to run on cluster .",
                    "runbook_url": "https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubedaemonsetmisscheduled",
                    "summary": "DaemonSet pods are misscheduled.",
                },
                "startsAt": "2026-05-30T22:07:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
            },
            {
                "status": "firing",
                "labels": {
                    "alertgroup": "kubernetes-apps",
                    "alertname": "KubeDaemonSetMisScheduled456",
                    "container": "kube-state-metrics",
                    "daemonset": "svclb-traefik-cfbcf9b2",
                    "endpoint": "http",
                    "instance": "10.42.2.49:8080",
                    "job": "kube-state-metrics",
                    "tgChatId": "-10000000000",
                    "namespace": "kube-system",
                    "pod": "victoria-metrics-kube-state-metrics-865d4cc775-rj5r5",
                    "prometheus": "monitoring/victoria-metrics-k8s",
                    "service": "victoria-metrics-kube-state-metrics",
                    "severity": "warning",
                },
                "annotations": {
                    "description": "1 Pods of DaemonSet kube-system/svclba-traefik-cfbcf9b2 are running where they are not supposed to run on cluster .",
                    "runbook_url": "https://runbooks.prometheus-operator.dev/runbooks/kubernetes/kubedaemonsetmisscheduled",
                    "summary": "DaemonSet pods are misscheduled.",
                },
                "startsAt": "2026-05-30T22:07:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
            },
        ],
    }
]

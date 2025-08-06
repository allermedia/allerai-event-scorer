locals {
  datasets = yamldecode(file("${path.module}/config/bigquery/datasets.yml"))
}

resource "google_bigquery_dataset" "datasets" {
  for_each = { for d in local.datasets : d.dataset_id => d }

  dataset_id = each.value.dataset_id
  location   = each.value.location
}

resource "google_bigquery_table" "tables" {
  for_each = {
    for pair in flatten([
      for dataset in local.datasets : [
        for table in dataset.tables : {
          key = "${dataset.dataset_id}.${table.table_id}"
          value = {
            dataset_id   = dataset.dataset_id
            table_id     = table.table_id
            schema_file  = try(table.schema_file, null)
            partitioning = try(table.time_partitioning, null)
          }
        }
      ]
    ]) : pair.key => pair.value
  }

  dataset_id = google_bigquery_dataset.datasets[each.value.dataset_id].dataset_id
  table_id   = each.value.table_id

  dynamic "schema" {
    for_each = each.value.schema_file != null ? [each.value.schema_file] : []
    content {
      schema = file(schema.value)
    }
  }

  dynamic "time_partitioning" {
    for_each = each.value.partitioning != null ? [each.value.partitioning] : []
    content {
      type  = time_partitioning.value.type
      field = try(time_partitioning.value.field, null)
    }
  }
}

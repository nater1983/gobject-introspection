/* GObject introspection: Property implementation
 *
 * Copyright (C) 2005 Matthias Clasen
 * Copyright (C) 2008,2009 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <glib.h>

#include <girepository.h>
#include "girepository-private.h"
#include "gitypelib-internal.h"

/**
 * SECTION:gipropertyinfo
 * @Short_description: Struct representing a property
 * @Title: GIPropertyInfo
 *
 * GIPropertyInfo represents a property. A property belongs to
 * either a #GIObjectInfo or a #GIInterfaceInfo.
 *
 * <refsect1 id="gi-gipropertyinfo.struct-hierarchy" role="struct_hierarchy">
 * <title role="struct_hierarchy.title">Struct hierarchy</title>
 * <synopsis>
 *   <link linkend="gi-GIBaseInfo">GIBaseInfo</link>
 *    +----GIPropertyInfo
 * </synopsis>
 * </refsect1>
 */

/**
 * g_property_info_get_flags:
 * @info: a #GIPropertyInfo
 *
 * Obtain the flags for this property info. See #GParamFags for
 * more information about possible flag values.
 *
 * Returns: the flags
 */
GParamFlags
g_property_info_get_flags (GIPropertyInfo *info)
{
  GParamFlags flags;
  GIRealInfo *rinfo = (GIRealInfo *)info;
  PropertyBlob *blob;

  g_return_val_if_fail (info != NULL, 0);
  g_return_val_if_fail (GI_IS_PROPERTY_INFO (info), 0);

  blob = (PropertyBlob *)&rinfo->typelib->data[rinfo->offset];

  flags = 0;

  if (blob->readable)
    flags = flags | G_PARAM_READABLE;

  if (blob->writable)
    flags = flags | G_PARAM_WRITABLE;

  if (blob->construct)
    flags = flags | G_PARAM_CONSTRUCT;

  if (blob->construct_only)
    flags = flags | G_PARAM_CONSTRUCT_ONLY;

  return flags;
}

/**
 * g_property_info_get_type:
 * @info: a #GIPropertyInfo
 *
 * Obtain the type information for the property @info.
 *
 * Returns: (transfer full): the #GITypeInfo, free it with
 * g_base_info_unref() when done.
 */
GITypeInfo *
g_property_info_get_type (GIPropertyInfo *info)
{
  GIRealInfo *rinfo = (GIRealInfo *)info;

  g_return_val_if_fail (info != NULL, NULL);
  g_return_val_if_fail (GI_IS_PROPERTY_INFO (info), NULL);

  return _g_type_info_new ((GIBaseInfo*)info,
                           rinfo->typelib,
                           rinfo->offset + G_STRUCT_OFFSET (PropertyBlob, type));
}

/**
 * g_property_info_get_ownership_transfer:
 * @info: a #GIPropertyInfo
 *
 * Obtain the ownership transfer for this property. See #GITransfer for more
 * information about transfer values.
 *
 * Returns: the transfer
 */
GITransfer
g_property_info_get_ownership_transfer (GIPropertyInfo *info)
{
  GIRealInfo *rinfo = (GIRealInfo *)info;
  PropertyBlob *blob;

  g_return_val_if_fail (info != NULL, -1);
  g_return_val_if_fail (GI_IS_PROPERTY_INFO (info), -1);

  blob = (PropertyBlob *)&rinfo->typelib->data[rinfo->offset];

  if (blob->transfer_ownership)
    return GI_TRANSFER_EVERYTHING;
  else if (blob->transfer_container_ownership)
    return GI_TRANSFER_CONTAINER;
  else
    return GI_TRANSFER_NOTHING;
}
